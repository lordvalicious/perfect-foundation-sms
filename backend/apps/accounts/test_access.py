from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone
from rest_framework.request import Request as DRFRequest
from rest_framework.test import (
    APIRequestFactory,
    APIClient,
    force_authenticate,
)

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffProfile,
)
from apps.accounts.access import (
    assert_campus_allowed,
    campus_access,
    is_global,
    user_allowed_campus_ids,
)
from apps.schools.models import Campus, School

from apps.students.models import Guardian, Student
from apps.teachers.models import Teacher


def make_user(username, role, school, extra_roles=None):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@test.edu",
        password="TestPass123!",
    )
    membership = InstitutionMembership.objects.create(
        user=user,
        institution=school,
    )
    RoleAssignment.objects.create(
        membership=membership,
        role=role,
    )
    for extra in extra_roles or []:
        RoleAssignment.objects.create(
            membership=membership,
            role=extra,
        )
    return user


def make_request(user, path="/api/events/"):
    factory = APIRequestFactory()
    django_request = factory.get(path)
    force_authenticate(django_request, user)
    return DRFRequest(django_request)


class IsGlobalTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus = Campus.objects.create(
            school=self.school,
            name="Main Campus",
        )

    def test_superuser_is_global(self):
        user = get_user_model().objects.create_superuser(
            username="root",
            email="root@test.edu",
            password="TestPass123!",
        )
        self.assertTrue(is_global(user))

    def test_global_roles(self):
        for role in (Role.SUPER_ADMIN, Role.ADMIN, Role.ACADEMIC):
            with self.subTest(role=role):
                user = make_user(f"g-{role}", role, self.school)
                self.assertTrue(is_global(user))

    def test_non_global_roles(self):
        for role in (
            Role.CAMPUS_ADMIN,
            Role.PRINCIPAL,
            Role.ACCOUNTANT,
            Role.TEACHER,
            Role.STAFF,
            Role.STUDENT,
            Role.PARENT,
        ):
            with self.subTest(role=role):
                user = make_user(f"ng-{role}", role, self.school)
                self.assertFalse(is_global(user))


class UserAllowedCampusTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus_a = Campus.objects.create(
            school=self.school,
            name="Campus A",
        )
        self.campus_b = Campus.objects.create(
            school=self.school,
            name="Campus B",
        )

    def test_super_admin_gets_every_active_campus(self):
        user = make_user("sadmin", Role.SUPER_ADMIN, self.school)
        self.assertEqual(
            user_allowed_campus_ids(user),
            {self.campus_a.pk, self.campus_b.pk},
        )

    def test_inactive_campus_excluded_for_global(self):
        Campus.objects.create(
            school=self.school,
            name="Closed Campus",
            status="inactive",
        )
        user = make_user("sadmin2", Role.SUPER_ADMIN, self.school)
        self.assertEqual(
            user_allowed_campus_ids(user),
            {self.campus_a.pk, self.campus_b.pk},
        )

    def test_campus_admin_scoped_to_primary_campus(self):
        user = make_user("cadmin", Role.CAMPUS_ADMIN, self.school)
        StaffProfile.objects.create(
            user=user,
            employee_number="STF-001",
            first_name="Campus",
            last_name="Admin",
            gender="male",
            primary_campus=self.campus_a,
        )
        self.assertEqual(
            user_allowed_campus_ids(user),
            {self.campus_a.pk},
        )

    def test_teacher_scoped_to_primary_campus(self):
        user = make_user("teacher", Role.TEACHER, self.school)
        Teacher.objects.create(
            user=user,
            employee_number="TCH-001",
            first_name="Teach",
            last_name="Er",
            gender="female",
            primary_campus=self.campus_a,
        )
        self.assertEqual(
            user_allowed_campus_ids(user),
            {self.campus_a.pk},
        )

    def test_student_scoped_to_primary_campus(self):
        user = make_user("student", Role.STUDENT, self.school)
        guardian = Guardian.objects.create(
            name="Guardian One",
            relationship="Father",
            phone="555-0200",
        )
        Student.objects.create(
            user=user,
            admission_number="STU-001",
            first_name="Stud",
            last_name="Ent",
            gender="male",
            primary_campus=self.campus_a,
            guardian=guardian,
        )
        self.assertEqual(
            user_allowed_campus_ids(user),
            {self.campus_a.pk},
        )

    def test_parent_scoped_via_children(self):
        user = make_user("parent", Role.PARENT, self.school)
        guardian = Guardian.objects.create(
            user=user,
            name="Parent One",
            relationship="Mother",
            phone="555-0100",
        )
        Student.objects.create(
            admission_number="STU-002",
            first_name="Child",
            last_name="One",
            gender="female",
            primary_campus=self.campus_b,
            guardian=guardian,
        )
        self.assertEqual(
            user_allowed_campus_ids(user),
            {self.campus_b.pk},
        )

    def test_user_with_no_profile_gets_empty_scope(self):
        user = make_user("nobody", Role.STAFF, self.school)
        self.assertEqual(user_allowed_campus_ids(user), set())


class CampusAccessTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus_a = Campus.objects.create(
            school=self.school,
            name="Campus A",
        )
        self.campus_b = Campus.objects.create(
            school=self.school,
            name="Campus B",
        )
        self.admin = make_user("cadmin", Role.CAMPUS_ADMIN, self.school)
        StaffProfile.objects.create(
            user=self.admin,
            employee_number="STF-002",
            first_name="Campus",
            last_name="Admin",
            gender="male",
            primary_campus=self.campus_a,
        )

    def test_campus_admin_can_request_own_campus(self):
        request = make_request(self.admin, f"/?campus={self.campus_a.pk}")
        result = campus_access(request)
        self.assertFalse(result["global"])
        self.assertEqual(
            result["requested"],
            self.campus_a.pk,
        )

    def test_campus_admin_denied_foreign_campus(self):
        request = make_request(self.admin, f"/?campus={self.campus_b.pk}")
        with self.assertRaises(PermissionDenied):
            campus_access(request)

    def test_campus_admin_without_param_scoped_to_own(self):
        request = make_request(self.admin, "/")
        result = campus_access(request)
        self.assertEqual(
            result["allowed_ids"],
            {self.campus_a.pk},
        )
        self.assertIsNone(result["requested"])

    def test_global_user_requesting_foreign_campus_allowed(self):
        admin = make_user("sadmin", Role.SUPER_ADMIN, self.school)
        request = make_request(admin, f"/?campus={self.campus_b.pk}")
        result = campus_access(request)
        self.assertTrue(result["global"])
        self.assertEqual(result["requested"], self.campus_b.pk)

    def test_global_user_denied_unknown_campus(self):
        admin = make_user("sadmin2", Role.SUPER_ADMIN, self.school)
        request = make_request(admin, "/?campus=9999")
        with self.assertRaises(PermissionDenied):
            campus_access(request)


class AssertCampusAllowedTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus_a = Campus.objects.create(
            school=self.school,
            name="Campus A",
        )
        self.campus_b = Campus.objects.create(
            school=self.school,
            name="Campus B",
        )
        self.admin = make_user("cadmin", Role.CAMPUS_ADMIN, self.school)
        StaffProfile.objects.create(
            user=self.admin,
            employee_number="STF-003",
            first_name="Campus",
            last_name="Admin",
            gender="male",
            primary_campus=self.campus_a,
        )

    def test_allowed_campus_passes(self):
        assert_campus_allowed(self.admin, self.campus_a.pk)

    def test_foreign_campus_rejected(self):
        with self.assertRaises(PermissionDenied):
            assert_campus_allowed(self.admin, self.campus_b.pk)

    def test_invalid_id_rejected(self):
        with self.assertRaises(PermissionDenied):
            assert_campus_allowed(self.admin, "not-an-id")

    def test_global_user_accepts_any_existing_campus(self):
        admin = make_user("sadmin", Role.SUPER_ADMIN, self.school)
        assert_campus_allowed(admin, self.campus_b.pk)

    def test_global_user_rejects_unknown_campus(self):
        admin = make_user("sadmin2", Role.SUPER_ADMIN, self.school)
        with self.assertRaises(PermissionDenied):
            assert_campus_allowed(admin, 9999)


class CampusIsolatedEventListTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus_a = Campus.objects.create(
            school=self.school,
            name="Campus A",
        )
        self.campus_b = Campus.objects.create(
            school=self.school,
            name="Campus B",
        )

        self.now = timezone.now()

        self.super_admin = make_user(
            "sadmin",
            Role.SUPER_ADMIN,
            self.school,
        )

        self.campus_admin = make_user(
            "cadmin",
            Role.CAMPUS_ADMIN,
            self.school,
        )
        StaffProfile.objects.create(
            user=self.campus_admin,
            employee_number="STF-004",
            first_name="Campus",
            last_name="Admin",
            gender="male",
            primary_campus=self.campus_a,
        )

        self.event_a = self._make_event("Event A", self.campus_a)
        self.event_b = self._make_event("Event B", self.campus_b)

        self.client = APIClient()

    def _make_event(self, title, campus):
        from apps.events.models import Event

        return Event.objects.create(
            school=self.school,
            campus=campus,
            title=title,
            start_datetime=self.now,
            end_datetime=self.now + timezone.timedelta(hours=1),
            status="published",
            created_by=self.super_admin,
        )

    def _as(self, user):
        self.client.force_authenticate(user=user)
        return self.client

    def test_campus_admin_only_sees_own_campus(self):
        client = self._as(self.campus_admin)

        response = client.get("/api/events/")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()]
        self.assertEqual(titles, ["Event A"])

    def test_campus_admin_denied_foreign_campus_param(self):
        client = self._as(self.campus_admin)

        response = client.get(
            f"/api/events/?campus={self.campus_b.pk}"
        )

        self.assertEqual(response.status_code, 403)

    def test_super_admin_sees_all_events(self):
        client = self._as(self.super_admin)

        response = client.get("/api/events/")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()]
        self.assertEqual(
            sorted(titles),
            ["Event A", "Event B"],
        )

    def test_super_admin_can_filter_by_campus(self):
        client = self._as(self.super_admin)

        response = client.get(
            f"/api/events/?campus={self.campus_b.pk}"
        )

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()]
        self.assertEqual(titles, ["Event B"])
