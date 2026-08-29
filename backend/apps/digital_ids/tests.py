from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffProfile,
)
from apps.digital_ids.models import IdCard
from apps.schools.models import Campus, School
from apps.students.models import Guardian, Student
from apps.teachers.models import Teacher


class DigitalIdsTestsBase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.school = School.objects.create(name="Test School")
        self.campus = Campus.objects.create(
            school=self.school,
            name="Main Campus",
        )

        self.admin = self._make_user("admin", Role.ADMIN)
        self.student_user = self._make_user("student", Role.STUDENT)

        self.guardian = Guardian.objects.create(
            institution=self.school,
            name="Test Parent",
        )
        self.student = Student.objects.create(
            admission_number="STU-001",
            first_name="Ali",
            gender="male",
            institution=self.school,
            primary_campus=self.campus,
            guardian=self.guardian,
            status="active",
        )
        self.teacher = Teacher.objects.create(
            employee_number="TCH-001",
            first_name="Uzma",
            last_name="Khan",
            gender="female",
            institution=self.school,
            primary_campus=self.campus,
            status="active",
        )
        self.staff_profile = StaffProfile.objects.create(
            user=self.student_user,
            institution=self.school,
            employee_number="STF-001",
            first_name="Imran",
            last_name="Ali",
            gender="male",
            primary_campus=self.campus,
            status="active",
        )

    def _make_user(self, username, role):
        user = get_user_model().objects.create_user(
            username=username,
            email=f"{username}@test.edu",
            password="TestPass123!",
        )
        membership = InstitutionMembership.objects.create(
            user=user,
            institution=self.school,
        )
        RoleAssignment.objects.create(
            membership=membership,
            role=role,
        )
        return user

    def login(self, username):
        self.client.force_login(get_user_model().objects.get(username=username))

    def _issue(self, **kwargs):
        values = {
            "holder_type": "student",
            "student": self.student.pk,
        }
        values.update(kwargs)
        return self.client.post("/api/digital-ids/cards/", values, format="json")


class DigitalCardTests(DigitalIdsTestsBase):
    def test_issue_student_card(self):
        self.login("admin")

        response = self._issue()

        self.assertEqual(response.status_code, 201, response.content)
        card = IdCard.objects.get()
        self.assertTrue(card.card_number.startswith("PF-"))
        self.assertEqual(card.barcode_data, card.card_number)
        self.assertEqual(card.campus_id, self.campus.pk)
        self.assertEqual(card.status, "active")
        self.assertIsNotNone(card.expiry_date)

    def test_reissue_revokes_previous_active(self):
        self.login("admin")
        self._issue()

        response = self._issue()

        self.assertEqual(response.status_code, 201, response.content)
        first = IdCard.objects.order_by("created_at").first()
        second = IdCard.objects.order_by("created_at").last()
        self.assertEqual(first.status, "revoked")
        self.assertEqual(second.status, "active")
        self.assertNotEqual(first.card_number, second.card_number)

    def test_issue_teacher_card_and_payload(self):
        self.login("admin")

        response = self.client.post(
            "/api/digital-ids/cards/",
            {
                "holder_type": "teacher",
                "teacher": self.teacher.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)

        card = IdCard.objects.get()
        payload_response = self.client.get(
            f"/api/digital-ids/cards/{card.pk}/payload/"
        )
        self.assertEqual(payload_response.status_code, 200)
        self.assertEqual(payload_response.data["holder_name"], "Uzma Khan")
        self.assertEqual(payload_response.data["holder_code"], "TCH-001")
        self.assertEqual(payload_response.data["barcode_data"], card.card_number)

    def test_issue_staff_card(self):
        self.login("admin")

        response = self.client.post(
            "/api/digital-ids/cards/",
            {
                "holder_type": "staff",
                "staff": self.staff_profile.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        card = IdCard.objects.get()
        self.assertEqual(card.holder_type, "staff")
        self.assertEqual(card.holder_code, "STF-001")

    def test_revoke_card(self):
        self.login("admin")
        self._issue()
        card = IdCard.objects.get()

        response = self.client.post(f"/api/digital-ids/cards/{card.pk}/revoke/")

        self.assertEqual(response.status_code, 200)
        card.refresh_from_db()
        self.assertEqual(card.status, "revoked")

    def test_student_role_denied(self):
        self.login("student")

        response = self._issue()

        self.assertEqual(response.status_code, 403)