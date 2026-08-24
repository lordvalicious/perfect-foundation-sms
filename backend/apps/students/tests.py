from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import InstitutionMembership, Role, RoleAssignment, User
from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, School, Section

from .models import (
	AdmissionApplication,
	Guardian,
	Enrollment,
	Student,
	StudentGuardian,
	StudentLeaveRequest,
	StudentLifecycleEvent,
)


class StudentLifecycleModelTests(TestCase):
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
		self.guardian = Guardian.objects.create(
			name="Test Parent",
			relationship="Father",
			phone="03000000000",
		)
		self.student = Student.objects.create(
			admission_number="ADM-001",
			first_name="Ali",
			gender="male",
			guardian=self.guardian,
		)
		self.admin = User.objects.create_user(
			username="academic-admin",
			email="academic-admin@example.com",
			password="test-password",
		)
		membership = InstitutionMembership.objects.create(
			user=self.admin,
			institution=self.school,
		)
		RoleAssignment.objects.create(
			membership=membership,
			role=Role.ADMIN,
		)

	def test_admission_application_exposes_applicant_name(self):
		application = AdmissionApplication.objects.create(
			application_number="APP-001",
			first_name="Sara",
			last_name="Khan",
			gender="female",
			guardian=self.guardian,
			campus=self.campus,
			academic_year=self.year,
			class_obj=self.class_obj,
			section=self.section,
		)

		self.assertEqual(application.applicant_name, "Sara Khan")

	def test_admission_application_rejects_wrong_section(self):
		other_class = Class.objects.create(unit=self.class_obj.unit, name="Grade 2")
		other_section = Section.objects.create(class_obj=other_class, name="A")
		application = AdmissionApplication(
			application_number="APP-002",
			first_name="Sara",
			gender="female",
			campus=self.campus,
			academic_year=self.year,
			class_obj=self.class_obj,
			section=other_section,
		)

		with self.assertRaises(ValidationError):
			application.full_clean()

	def test_student_can_have_multiple_guardians_but_not_duplicate_links(self):
		second_guardian = Guardian.objects.create(
			name="Test Mother",
			relationship="Mother",
			phone="03111111111",
		)
		StudentGuardian.objects.create(
			student=self.student,
			guardian=self.guardian,
			relationship="Father",
			is_primary=True,
		)
		StudentGuardian.objects.create(
			student=self.student,
			guardian=second_guardian,
			relationship="Mother",
		)

		self.assertEqual(self.student.guardian_links.count(), 2)
		with self.assertRaises(IntegrityError):
			StudentGuardian.objects.create(
				student=self.student,
				guardian=self.guardian,
				relationship="Father",
			)

	def test_lifecycle_event_preserves_reason_and_student(self):
		event = StudentLifecycleEvent.objects.create(
			student=self.student,
			event_type="withdrawn",
			effective_date=date(2026, 9, 1),
			reason="Family relocation",
		)

		self.assertEqual(event.student, self.student)
		self.assertEqual(event.reason, "Family relocation")

	def test_leave_request_rejects_reverse_date_range(self):
		leave = StudentLeaveRequest(
			student=self.student,
			start_date=date(2026, 9, 10),
			end_date=date(2026, 9, 9),
			reason="Medical appointment",
		)

		with self.assertRaises(ValidationError):
			leave.full_clean()

	def test_enrollment_rejects_class_from_another_campus(self):
		other_campus = Campus.objects.create(
			school=self.school,
			name="North Campus",
		)
		other_unit = AcademicUnit.objects.create(
			campus=other_campus,
			name="Secondary",
		)
		other_class = Class.objects.create(unit=other_unit, name="Grade 2")
		other_section = Section.objects.create(class_obj=other_class, name="A")
		enrollment = Enrollment(
			student=self.student,
			academic_year=self.year,
			campus=self.campus,
			class_obj=other_class,
			section=other_section,
		)

		with self.assertRaises(ValidationError):
			enrollment.full_clean()

	def test_enrollment_allows_only_one_record_per_student_and_year(self):
		Enrollment.objects.create(
			student=self.student,
			academic_year=self.year,
			campus=self.campus,
			class_obj=self.class_obj,
			section=self.section,
			roll_number="18",
		)

		with self.assertRaises(ValidationError):
			Enrollment.objects.create(
				student=self.student,
				academic_year=self.year,
				campus=self.campus,
				class_obj=self.class_obj,
				section=self.section,
			)

		self.assertEqual(
			Enrollment.objects.get(
				student=self.student,
				academic_year=self.year,
			).roll_number,
			"18",
		)

	def test_admission_application_rejects_year_from_another_school(self):
		other_school = School.objects.create(name="Other School")
		other_year = AcademicYear.objects.create(
			school=other_school,
			name="2026-2027",
			start_date=date(2026, 8, 1),
			end_date=date(2027, 7, 31),
		)
		application = AdmissionApplication(
			application_number="APP-003",
			first_name="Hamza",
			gender="male",
			campus=self.campus,
			academic_year=other_year,
			class_obj=self.class_obj,
			section=self.section,
		)

		with self.assertRaises(ValidationError):
			application.full_clean()

	def test_admission_acceptance_creates_student_guardian_link_and_enrollment(self):
		application = AdmissionApplication.objects.create(
			application_number="APP-ACCEPT-001",
			first_name="Sara",
			last_name="Khan",
			gender="female",
			guardian=self.guardian,
			campus=self.campus,
			academic_year=self.year,
			class_obj=self.class_obj,
			section=self.section,
			status="submitted",
		)
		self.client.force_login(self.admin)

		response = self.client.post(
			f"/api/students/admissions/{application.pk}/accept/",
			{"admission_number": "ADM-ACCEPT-001"},
		)

		self.assertEqual(response.status_code, 201)
		application.refresh_from_db()
		self.assertEqual(application.status, "accepted")
		student = Student.objects.get(admission_number="ADM-ACCEPT-001")
		self.assertTrue(
			StudentGuardian.objects.filter(
				student=student,
				guardian=self.guardian,
				is_primary=True,
			).exists()
		)
		self.assertTrue(
			Enrollment.objects.filter(
				student=student,
				academic_year=self.year,
				status="active",
			).exists()
		)

	def test_guardian_my_endpoint_returns_linked_parent_profile(self):
		parent = User.objects.create_user(
			username="parent-user",
			email="parent@example.com",
			password="test-password",
		)
		self.guardian.user = parent
		self.guardian.save(update_fields=["user", "updated_at"])
		membership = InstitutionMembership.objects.create(
			user=parent,
			institution=self.school,
		)
		RoleAssignment.objects.create(
			membership=membership,
			role=Role.PARENT,
		)
		self.client.force_login(parent)

		response = self.client.get("/api/students/guardians/me/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["id"], self.guardian.pk)
