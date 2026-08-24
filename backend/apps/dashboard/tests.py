from datetime import date
import json

from django.test import TestCase

from apps.accounts.models import User
from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, Section, School
from apps.students.models import Enrollment, Guardian, Student


class AcademicDashboardTests(TestCase):
	def test_overview_returns_academic_counts_for_authenticated_manager(self):
		school = School.objects.create(name="Test School")
		campus = Campus.objects.create(school=school, name="Main Campus")
		unit = AcademicUnit.objects.create(campus=campus, name="Primary")
		class_obj = Class.objects.create(unit=unit, name="Grade 1")
		section = Section.objects.create(class_obj=class_obj, name="A")
		year = AcademicYear.objects.create(
			school=school,
			name="2026-2027",
			start_date=date(2026, 8, 1),
			end_date=date(2027, 7, 31),
		)
		guardian = Guardian.objects.create(
			name="Test Parent",
			relationship="Father",
			phone="03000000000",
		)
		student = Student.objects.create(
			admission_number="ADM-DASH-001",
			first_name="Ali",
			gender="male",
			guardian=guardian,
			status="active",
		)
		Enrollment.objects.create(
			student=student,
			academic_year=year,
			campus=campus,
			class_obj=class_obj,
			section=section,
		)
		user = User.objects.create_superuser(
			username="dashboard-admin",
			email="dashboard-admin@example.com",
			password="test-password",
		)
		self.client.force_login(user)

		response = self.client.get("/api/dashboard/overview/")

		self.assertEqual(response.status_code, 200)
		data = json.loads(response.content)
		self.assertEqual(data["students"], {"total": 1, "active": 1})
		self.assertEqual(data["classes"], 1)
		self.assertEqual(data["sections"], 1)
		self.assertEqual(data["enrollments"], 1)
