from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
)
from apps.events.models import Event
from apps.schools.models import School


class EventTestsBase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.school = School.objects.create(
            name="Test School",
            city="Test City",
        )

        self.admin = get_user_model().objects.create_user(
            username="admin",
            email="admin@test.edu",
            password="TestPass123!",
        )

        membership = InstitutionMembership.objects.create(
            user=self.admin,
            institution=self.school,
        )

        RoleAssignment.objects.create(
            membership=membership,
            role=Role.ADMIN,
        )

        self.student = get_user_model().objects.create_user(
            username="student",
            email="student@test.edu",
            password="TestPass123!",
        )

        student_membership = InstitutionMembership.objects.create(
            user=self.student,
            institution=self.school,
        )

        RoleAssignment.objects.create(
            membership=student_membership,
            role=Role.STUDENT,
        )

    def login(self, username, password="TestPass123!"):
        self.client.post(
            "/api/auth/csrf/",
            {},
            format="json",
        )
        self.client.post(
            "/api/auth/login/",
            {
                "username": username,
                "password": password,
            },
            format="json",
        )

    def create_event(self, status="published"):
        return Event.objects.create(
            school=self.school,
            title="Sports Day",
            description="Annual sports event",
            location="Main Ground",
            start_datetime="2026-09-01T09:00:00Z",
            end_datetime="2026-09-01T17:00:00Z",
            status=status,
            created_by=self.admin,
        )


class EventTests(EventTestsBase):
    def test_requires_authentication(self):
        response = self.client.get("/api/events/")

        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_event(self):
        self.login("admin")

        response = self.client.post(
            "/api/events/",
            {
                "title": "Science Fair",
                "description": "Showcase of projects",
                "location": "Hall A",
                "start_datetime": "2026-10-01T09:00:00Z",
                "end_datetime": "2026-10-01T15:00:00Z",
                "status": "published",
                "audiences": [
                    {
                        "audience_type": "students",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        event = Event.objects.get(title="Science Fair")

        self.assertEqual(event.school, self.school)
        self.assertEqual(event.created_by, self.admin)
        self.assertEqual(
            event.audiences.first().audience_type,
            "students",
        )

    def test_student_only_sees_published_events(self):
        self.create_event(status="draft")
        self.create_event(status="published")

        self.login("student")

        response = self.client.get("/api/events/")

        self.assertEqual(response.status_code, 200)

        events = response.json()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Sports Day")

    def test_event_creation_is_audited(self):
        from apps.audit.models import AuditLog

        self.login("admin")

        self.client.post(
            "/api/events/",
            {
                "title": "Audited Event",
                "start_datetime": "2026-10-01T09:00:00Z",
                "end_datetime": "2026-10-01T15:00:00Z",
            },
            format="json",
        )

        log = AuditLog.objects.filter(
            action="create",
            model_name="Event",
        ).first()

        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.object_repr, "Audited Event")
