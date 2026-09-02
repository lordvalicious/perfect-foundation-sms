from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import InstitutionMembership, Role, RoleAssignment

from .models import (
	AcademicUnit,
	AcademicYear,
	Campus,
	Class,
	School,
	Section,
	Subject,
	SubjectOffering,
)


class AcademicStructureModelTests(TestCase):
	def setUp(self):
		self.school = School.objects.create(name="Test School")
		self.campus = Campus.objects.create(school=self.school, name="Main Campus")
		unit = AcademicUnit.objects.create(campus=self.campus, name="Primary")
		self.class_obj = Class.objects.create(unit=unit, name="Grade 1")
		self.section = Section.objects.create(class_obj=self.class_obj, name="A")
		self.year = AcademicYear.objects.create(
			school=self.school,
			name="2026-2027",
			start_date=date(2026, 8, 1),
			end_date=date(2027, 7, 31),
		)
		self.subject = Subject.objects.create(
			institution=self.school,
			name="English",
			code="ENG-SCHOOL",
		)

	def test_section_names_are_unique_within_a_class(self):
		duplicate = Section(class_obj=self.class_obj, name="A")

		with self.assertRaises(ValidationError):
			duplicate.full_clean()

	def test_subject_offering_is_unique_for_class_and_year(self):
		SubjectOffering.objects.create(
			subject=self.subject,
			class_obj=self.class_obj,
			academic_year=self.year,
		)
		duplicate = SubjectOffering(
			subject=self.subject,
			class_obj=self.class_obj,
			academic_year=self.year,
		)

		with self.assertRaises(ValidationError):
			duplicate.full_clean()


class TenantBrandingApiTests(TestCase):
	def setUp(self):
		self.school_a = School.objects.create(name="School A", code="school-a")
		self.school_b = School.objects.create(name="School B", code="school-b")
		self.user = get_user_model().objects.create_user(
			username="admin-a",
			email="admin-a@test.edu",
			password="TestPass123!",
		)
		membership = InstitutionMembership.objects.create(
			user=self.user,
			institution=self.school_a,
		)
		RoleAssignment.objects.create(membership=membership, role=Role.ADMIN)
		self.client = APIClient()

	def test_branding_is_resolved_from_authenticated_tenant(self):
		self.client.login(username="admin-a", password="TestPass123!")
		response = self.client.get("/api/schools/branding/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["school_code"], "school-a")
		self.assertEqual(response.data["school_name"], "School A")

	def test_branding_update_cannot_touch_another_tenant(self):
		self.client.login(username="admin-a", password="TestPass123!")
		response = self.client.put(
			"/api/schools/branding/",
			{"school_name": "Changed A"},
			format="multipart",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(School.objects.get(pk=self.school_a.pk).name, "Changed A")
		self.assertEqual(School.objects.get(pk=self.school_b.pk).name, "School B")

	def test_public_config_requires_a_valid_active_code(self):
		response = self.client.get(
			"/api/schools/tenant-config/?school_code=school-b"
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["school_name"], "School B")

		missing = self.client.get(
			"/api/schools/tenant-config/?school_code=missing"
		)
		self.assertEqual(missing.status_code, 404)
