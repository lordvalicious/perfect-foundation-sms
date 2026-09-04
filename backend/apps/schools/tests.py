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


class SectionDetailApiTests(TestCase):
	def setUp(self):
		self.school_a = School.objects.create(name="School A")
		self.campus_a = Campus.objects.create(school=self.school_a, name="Campus A")
		self.unit_a = AcademicUnit.objects.create(campus=self.campus_a, name="Unit A")
		self.class_a = Class.objects.create(unit=self.unit_a, name="Grade 1")
		self.section_a = Section.objects.create(class_obj=self.class_a, name="A")

		self.school_b = School.objects.create(name="School B")
		self.campus_b = Campus.objects.create(school=self.school_b, name="Campus B")
		self.unit_b = AcademicUnit.objects.create(campus=self.campus_b, name="Unit B")
		self.class_b = Class.objects.create(unit=self.unit_b, name="Grade 1")
		self.section_b = Section.objects.create(class_obj=self.class_b, name="A")

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
		self.client.login(username="admin-a", password="TestPass123!")

	def test_update_section(self):
		response = self.client.patch(
			f"/api/schools/sections/{self.section_a.pk}/",
			{"capacity": 45},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.section_a.refresh_from_db()
		self.assertEqual(self.section_a.capacity, 45)

	def test_update_enforces_unique_name_within_class(self):
		other = Section.objects.create(class_obj=self.class_a, name="B")
		response = self.client.patch(
			f"/api/schools/sections/{other.pk}/",
			{"name": "A"},
			format="json",
		)
		self.assertEqual(response.status_code, 400)
		self.section_a.refresh_from_db()
		other.refresh_from_db()
		self.assertEqual(other.name, "B")

	def test_delete_section(self):
		section_to_delete = Section.objects.create(class_obj=self.class_a, name="C")
		response = self.client.delete(
			f"/api/schools/sections/{section_to_delete.pk}/"
		)
		self.assertEqual(response.status_code, 204)
		self.assertFalse(
			Section.objects.filter(pk=section_to_delete.pk).exists()
		)

	def test_cannot_access_section_from_another_tenant(self):
		for method, kwargs in [
			("get", {}),
			("patch", {"capacity": 30}),
			("delete", {}),
		]:
			response = getattr(self.client, method)(
				f"/api/schools/sections/{self.section_b.pk}/",
				**kwargs,
			)
			self.assertEqual(
				response.status_code,
				404,
				f"{method} on foreign section",
			)
