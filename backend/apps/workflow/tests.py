from itertools import count

from django.test import TestCase
from rest_framework import status as http_status
from rest_framework.test import APIClient

from apps.accounts.models import InstitutionMembership, Role, RoleAssignment, User
from apps.communication.models import Announcement
from apps.schools.models import Campus, School
from apps.teachers.models import Teacher
from apps.workflow import services
from apps.workflow.models import (
    WorkflowApproval,
    WorkflowDefinition,
    WorkflowInstance,
)

_school_seq = count(1)
_user_seq = count(1)
_obj_seq = count(1)

ANNOUNCEMENT_TYPE = "communication.announcement"


def _definition(approval_steps=None, extra=None):
    return WorkflowDefinition.objects.create(
        name="Announcement Approval",
        slug="communication.announcement.approval",
        object_type=ANNOUNCEMENT_TYPE,
        states=["draft", "pending_approval", "approved", "rejected", "cancelled"],
        initial_state="draft",
        approval_steps=approval_steps or [Role.ADMIN],
        transitions={
            "submit": {"from": ["draft"], "to": "pending_approval"},
            "approve": {"from": ["pending_approval"], "to": "approved"},
            "reject": {"from": ["pending_approval"], "to": "rejected"},
            "cancel": {"from": ["draft", "pending_approval"], "to": "cancelled"},
            "restart": {"from": ["rejected"], "to": "draft"},
            **(extra or {}),
        },
    )


class WorkflowEngineTests(TestCase):
    def setUp(self):
        n = next(_school_seq)
        self.school = School.objects.create(name=f"Workflow High {n}")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")
        self.definition = _definition()

        self.manager = self._make_user(Role.ADMIN, "manager")
        self.hr = self._make_user(Role.HR, "hr")
        self.submitter = self._make_user(Role.TEACHER, "submitter")

        self.announcement = Announcement.objects.create(
            institution=self.school,
            title="Campus Closure",
            message="School closes early on Friday.",
        )
        self.obj_id = next(_obj_seq)

    def _make_user(self, role, label):
        n = next(_user_seq)
        user = User.objects.create_user(
            username=f"{label}{n}",
            email=f"{label}{n}@test.edu",
            password="TestPass123!",
        )
        membership = InstitutionMembership.objects.create(user=user, institution=self.school)
        RoleAssignment.objects.create(membership=membership, role=role)
        return user

    def _start(self, actor=None, object_type=None):
        return services.start(
            object_type or ANNOUNCEMENT_TYPE,
            self.obj_id,
            institution=self.school,
            campus=self.campus,
            actor=actor or self.submitter,
        )

    def test_start_records_initial_transition(self):
        instance = self._start()
        self.assertEqual(instance.current_state, "draft")
        self.assertFalse(instance.is_terminal)
        self.assertEqual(instance.transitions.count(), 1)
        first = instance.transitions.first()
        self.assertEqual(first.action, "start")
        self.assertEqual(first.to_state, "draft")
        self.assertEqual(first.actor, self.submitter)

    def test_submit_moves_to_pending_and_creates_approvals(self):
        instance = self._start()
        result = services.submit(instance, self.submitter, "Please review.")
        self.assertEqual(result.current_state, "pending_approval")
        self.assertIsNotNone(result.submitted_at)
        approvals = list(result.approvals.all())
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0].role, Role.ADMIN)
        self.assertEqual(approvals[0].status, WorkflowApproval.Status.PENDING)

    def test_approve_requires_the_queued_role(self):
        instance = self._start()
        services.submit(instance, self.submitter)

        with self.assertRaises(services.WorkflowPermissionError):
            services.approve(instance, self.submitter)
        with self.assertRaises(services.WorkflowPermissionError):
            services.approve(instance, self.hr)

        result = services.approve(instance, self.manager, "Approved.")
        self.assertEqual(result.current_state, "approved")
        self.assertTrue(result.is_terminal)
        self.assertIsNotNone(result.completed_at)
        approval = result.approvals.first()
        self.assertEqual(approval.status, WorkflowApproval.Status.APPROVED)
        self.assertEqual(approval.approver, self.manager)
        last = result.transitions.first()
        self.assertEqual(last.action, "approve")
        self.assertEqual(last.from_state, "pending_approval")
        self.assertEqual(last.to_state, "approved")
        self.assertEqual(last.actor, self.manager)

    def test_reject_moves_to_rejected(self):
        instance = self._start()
        services.submit(instance, self.submitter)
        result = services.reject(instance, self.manager, "Missing details.")
        self.assertEqual(result.current_state, "rejected")
        self.assertEqual(result.approvals.first().status, WorkflowApproval.Status.REJECTED)

    def test_restart_after_rejection_resubmits(self):
        instance = self._start()
        services.submit(instance, self.submitter)
        services.reject(instance, self.manager)
        services.perform(instance, self.submitter, "restart", "Fixed.")
        self.assertEqual(instance.current_state, "draft")
        services.submit(instance, self.submitter)
        self.assertEqual(instance.current_state, "pending_approval")
        self.assertEqual(instance.approvals.filter(status=WorkflowApproval.Status.PENDING).count(), 1)

    def test_two_step_approval_needs_both_approvers(self):
        self.definition.delete()
        self.definition = _definition(approval_steps=[Role.HR, Role.ADMIN])
        instance = self._start()
        services.submit(instance, self.submitter)

        services.approve(instance, self.hr)
        self.assertEqual(instance.current_state, "pending_approval")

        result = services.approve(instance, self.manager)
        self.assertEqual(result.current_state, "approved")
        statuses = list(result.approvals.values_list("status", flat=True))
        self.assertEqual(statuses, [WorkflowApproval.Status.APPROVED, WorkflowApproval.Status.APPROVED])

    def test_rejection_skips_remaining_steps(self):
        self.definition.delete()
        self.definition = _definition(approval_steps=[Role.HR, Role.ADMIN])
        instance = self._start()
        services.submit(instance, self.submitter)
        services.reject(instance, self.hr)
        self.assertEqual(instance.current_state, "rejected")
        statuses = list(instance.approvals.values_list("status", flat=True))
        self.assertEqual(statuses, [WorkflowApproval.Status.REJECTED, WorkflowApproval.Status.SKIPPED])

    def test_invalid_transitions_are_rejected(self):
        instance = self._start()
        with self.assertRaises(services.WorkflowError):
            services.approve(instance, self.manager)
        with self.assertRaises(services.WorkflowError):
            services.perform(instance, self.manager, "explode")
        self.assertEqual(instance.current_state, "draft")
        self.assertEqual(instance.transitions.count(), 1)

    def test_no_active_definition_cannot_start(self):
        other_type = "communication.poll"
        self.assertFalse(WorkflowDefinition.objects.filter(object_type=other_type).exists())
        with self.assertRaises(services.WorkflowError):
            services.start(other_type, self.obj_id, actor=self.submitter)

    def test_history_is_append_only_audit(self):
        instance = self._start()
        services.submit(instance, self.submitter, "Please review.")
        services.approve(instance, self.manager, "Looks good.")
        history = list(instance.transitions.order_by("created_at"))
        self.assertEqual([h.action for h in history], ["start", "submit", "approve"])
        self.assertEqual([h.to_state for h in history], ["draft", "pending_approval", "approved"])

    def test_pending_approvals_for_user(self):
        instance = self._start()
        services.submit(instance, self.submitter)
        manager_queue = services.pending_approvals_for_user(self.manager, institution=self.school)
        self.assertEqual(len(manager_queue), 1)
        self.assertEqual(manager_queue[0].instance_id, instance.id)
        self.assertEqual(services.pending_approvals_for_user(self.submitter, institution=self.school), [])
        self.assertEqual(services.pending_approvals_for_user(self.hr, institution=self.school), [])


class WorkflowApiTests(TestCase):
    def setUp(self):
        n = next(_school_seq)
        self.school_a = School.objects.create(name=f"School A {n}")
        self.school_b = School.objects.create(name=f"School B {n}")
        self.campus_a = Campus.objects.create(school=self.school_a, name="Main A")
        self.campus_b = Campus.objects.create(school=self.school_b, name="Main B")

        self.admin_a = self._make_user(Role.ADMIN, self.school_a, "admin_a")
        self.manager_b = self._make_user(Role.ADMIN, self.school_b, "manager_b")
        self.teacher_a = self._make_user(Role.TEACHER, self.school_a, "teacher_a")
        self.hr_a = self._make_user(Role.HR, self.school_a, "hr_a")

        self.definition_a = _definition(approval_steps=[Role.HR, Role.ADMIN])

        Announcement.objects.create(
            institution=self.school_a,
            title="Assembly",
            message="All staff attend assembly.",
        )

        self.client = APIClient()

    def _make_user(self, role, school, label):
        n = next(_user_seq)
        user = User.objects.create_user(
            username=f"{label}{n}",
            email=f"{label}{n}@test.edu",
            password="TestPass123!",
        )
        membership = InstitutionMembership.objects.create(user=user, institution=school)
        RoleAssignment.objects.create(membership=membership, role=role)
        return user

    def _authed(self, user):
        self.client.force_authenticate(user=user)
        return self.client

    def _create_instance(self, user, object_id=None, campus=None, definition_slug="communication.announcement.approval"):
        payload = {
            "definition_slug": definition_slug,
            "object_type": ANNOUNCEMENT_TYPE,
            "object_id": object_id or next(_obj_seq),
        }
        if campus is not None:
            payload["campus"] = campus.id if hasattr(campus, "id") else campus
        response = self._authed(user).post(
            "/api/workflow/instances/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED, response.content)
        return response.data

    def test_anonymous_is_rejected(self):
        response = self.client.get("/api/workflow/definitions/")
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_list_definitions(self):
        response = self._authed(self.admin_a).get(
            "/api/workflow/definitions/",
            {"object_type": ANNOUNCEMENT_TYPE},
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["slug"], "communication.announcement.approval")

    def test_create_instance_and_run_full_flow(self):
        data = self._create_instance(self.admin_a)
        instance_id = data["id"]
        self.assertEqual(data["current_state"], "draft")

        detail = self.client.get(f"/api/workflow/instances/{instance_id}/")
        self.assertEqual(detail.status_code, http_status.HTTP_200_OK)
        self.assertEqual(detail.data["object_type"], ANNOUNCEMENT_TYPE)
        self.assertEqual(len(detail.data["transitions"]), 1)
        self.assertEqual(len(detail.data["approvals"]), 0)

        submit = self.client.post(
            f"/api/workflow/instances/{instance_id}/action/",
            {"action": "submit", "comment": "Please review."},
            format="json",
        )
        self.assertEqual(submit.status_code, http_status.HTTP_200_OK, submit.content)
        self.assertEqual(submit.data["current_state"], "pending_approval")
        self.assertEqual(len(submit.data["approvals"]), 2)

        first = self._authed(self.hr_a).post(
            f"/api/workflow/instances/{instance_id}/action/",
            {"action": "approve", "comment": "HR approved."},
            format="json",
        )
        self.assertEqual(first.status_code, http_status.HTTP_200_OK, first.content)
        self.assertEqual(first.data["current_state"], "pending_approval")

        second = self._authed(self.admin_a).post(
            f"/api/workflow/instances/{instance_id}/action/",
            {"action": "approve", "comment": "Admin approved."},
            format="json",
        )
        self.assertEqual(second.status_code, http_status.HTTP_200_OK, second.content)
        self.assertEqual(second.data["current_state"], "approved")

        history = self.client.get(f"/api/workflow/instances/{instance_id}/history/")
        self.assertEqual(history.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(history.data["results"]), 4)

    def test_approval_action_is_role_denied(self):
        data = self._create_instance(self.admin_a)
        instance = WorkflowInstance.objects.get(pk=data["id"])
        services.submit(instance, self.admin_a)

        response = self._authed(self.teacher_a).post(
            f"/api/workflow/instances/{instance.id}/action/",
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN, response.content)

    def test_unknown_action_is_rejected(self):
        data = self._create_instance(self.admin_a)
        response = self._authed(self.admin_a).post(
            f"/api/workflow/instances/{data['id']}/action/",
            {"action": "explode"},
            format="json",
        )
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST, response.content)

    def test_pending_approvals_endpoint(self):
        data = self._create_instance(self.admin_a)
        instance = WorkflowInstance.objects.get(pk=data["id"])
        services.submit(instance, self.admin_a)

        queue = self._authed(self.hr_a).get("/api/workflow/approvals/")
        self.assertEqual(queue.status_code, http_status.HTTP_200_OK, queue.content)
        self.assertEqual(len(queue.data), 1)
        self.assertEqual(queue.data[0]["role"], Role.HR)
        self.assertEqual(queue.data[0]["instance"], instance.id)

        mine = self._authed(self.teacher_a).get("/api/workflow/approvals/")
        self.assertEqual(len(mine.data), 0)

    def test_decide_approval_endpoint(self):
        data = self._create_instance(self.admin_a)
        instance = WorkflowInstance.objects.get(pk=data["id"])
        services.submit(instance, self.admin_a)

        hr_approval = instance.approvals.get(role=Role.HR)
        response = self._authed(self.hr_a).post(
            f"/api/workflow/approvals/{hr_approval.id}/decide/",
            {"decision": "approve", "comment": "Approved by HR."},
            format="json",
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK, response.content)
        self.assertEqual(response.data["current_state"], "pending_approval")

        admin_approval = instance.approvals.get(role=Role.ADMIN)
        response = self._authed(self.admin_a).post(
            f"/api/workflow/approvals/{admin_approval.id}/decide/",
            {"decision": "approve", "comment": "Approved by admin."},
            format="json",
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK, response.content)
        self.assertEqual(response.data["current_state"], "approved")
        instance.refresh_from_db()
        statuses = list(instance.approvals.values_list("status", flat=True))
        self.assertEqual(statuses, [WorkflowApproval.Status.APPROVED, WorkflowApproval.Status.APPROVED])

    def test_decide_wrong_step_is_rejected(self):
        data = self._create_instance(self.admin_a)
        instance = WorkflowInstance.objects.get(pk=data["id"])
        services.submit(instance, self.admin_a)

        admin_approval = instance.approvals.get(role=Role.ADMIN)
        response = self._authed(self.hr_a).post(
            f"/api/workflow/approvals/{admin_approval.id}/decide/",
            {"decision": "approve"},
            format="json",
        )
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST, response.content)

    def test_institution_isolation(self):
        data = self._create_instance(self.admin_a)
        instance_id = data["id"]

        hidden = self._authed(self.manager_b).get(f"/api/workflow/instances/{instance_id}/")
        self.assertEqual(hidden.status_code, http_status.HTTP_404_NOT_FOUND)

        other = self._authed(self.manager_b).get("/api/workflow/instances/")
        self.assertEqual(other.status_code, http_status.HTTP_200_OK)
        self.assertEqual(other.data["count"], 0)
        for row in other.data["results"]:
            self.assertNotEqual(row["id"], instance_id)

    def test_campus_scoping_for_non_global_user(self):
        second_campus = Campus.objects.create(school=self.school_a, name="Campus Two")
        first = self._create_instance(self.admin_a, campus=self.campus_a)
        second = self._create_instance(self.admin_a, campus=second_campus)

        teacher = self._make_user(Role.TEACHER, self.school_a, "teacher_campus")
        Teacher.objects.create(
            user=teacher,
            employee_number="EMP-CAMP-001",
            first_name="Teacher",
            last_name="Campus",
            gender="other",
            primary_campus=second_campus,
        )

        response = self._authed(teacher).get("/api/workflow/instances/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK, response.content)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(second["id"], ids)
        self.assertNotIn(first["id"], ids)