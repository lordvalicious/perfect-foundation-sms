from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffAttendance,
    StaffAttendanceCorrection,
    StaffProfile,
)
from apps.schools.models import Campus, School


class StaffAttendanceBase(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")

        self.user = get_user_model().objects.create_user(
            username="staff-attendance-admin",
            email="admin@test.edu",
            password="TestPass123!",
        )
        membership = InstitutionMembership.objects.create(
            user=self.user,
            institution=self.school,
        )
        RoleAssignment.objects.create(
            membership=membership,
            role=Role.ADMIN,
        )

        self.staff = StaffProfile.objects.create(
            institution=self.school,
            employee_number="EMP-001",
            first_name="Ayesha",
            last_name="Khan",
            gender="female",
            primary_campus=self.campus,
        )

        self.attendance = StaffAttendance.objects.create(
            institution=self.school,
            staff=self.staff,
            date=date(2026, 9, 1),
            status="present",
            check_in=time(8, 0),
            check_out=time(16, 0),
            marked_by=self.user,
        )


class StaffAttendanceModelTests(StaffAttendanceBase):
    def test_working_hours_computed(self):
        self.assertEqual(
            self.attendance.working_hours,
            timedelta(hours=8),
        )

    def test_working_hours_none_when_missing_timestamps(self):
        attendance = StaffAttendance.objects.create(
            institution=self.school,
            staff=self.staff,
            date=date(2026, 9, 2),
            status="present",
            marked_by=self.user,
        )
        self.assertIsNone(attendance.working_hours)


class StaffAttendanceCorrectionTests(StaffAttendanceBase):
    def test_correction_preserves_old_and_new_values(self):
        correction = StaffAttendanceCorrection.objects.create(
            attendance=self.attendance,
            staff=self.staff,
            institution=self.school,
            from_status=self.attendance.status,
            to_status="late",
            from_check_in=self.attendance.check_in,
            to_check_in=time(9, 30),
            from_check_out=self.attendance.check_out,
            to_check_out=self.attendance.check_out,
            reason="Manual correction",
            corrected_by=self.user,
        )

        self.assertEqual(correction.from_status, "present")
        self.assertEqual(correction.to_status, "late")
        self.assertEqual(correction.from_check_in, time(8, 0))
        self.assertEqual(correction.to_check_in, time(9, 30))
        self.assertEqual(correction.corrected_by, self.user)
        self.assertIsNotNone(correction.corrected_at)
        self.assertEqual(correction.reason, "Manual correction")

    def test_correction_is_immutable_audit_history(self):
        StaffAttendanceCorrection.objects.create(
            attendance=self.attendance,
            staff=self.staff,
            institution=self.school,
            from_status="present",
            to_status="late",
            reason="Late arrival",
            corrected_by=self.user,
        )
        StaffAttendanceCorrection.objects.create(
            attendance=self.attendance,
            staff=self.staff,
            institution=self.school,
            from_status="late",
            to_status="present",
            reason="Reverted",
            corrected_by=self.user,
        )

        self.assertEqual(self.attendance.corrections.count(), 2)
        statuses = list(
            self.attendance.corrections.values_list("to_status", flat=True)
        )
        self.assertIn("late", statuses)
        self.assertIn("present", statuses)

    def test_correction_rejects_invalid_status(self):
        correction = StaffAttendanceCorrection(
            attendance=self.attendance,
            staff=self.staff,
            institution=self.school,
            from_status="present",
            to_status="not-a-status",
            reason="bad",
            corrected_by=self.user,
        )
        with self.assertRaises(ValidationError):
            correction.full_clean()
