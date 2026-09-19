"""F7 remediation: public transfer-certificate verification endpoint tests."""

from datetime import date

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import Role
from apps.accounts.test_access import make_user
from apps.schools.models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
)
from apps.students.models import (
    Enrollment,
    Guardian,
    Student,
    TransferCertificate,
)

PUBLIC_FIELDS = {
    "certificate_number",
    "student_name",
    "campus",
    "issued_at",
    "status",
}

SENSITIVE_FIELDS = [
    "admission_number",
    "date_of_birth",
    "gender",
    "guardian_name",
    "guardian_relationship",
    "guardian_phone",
    "academic_year",
    "class_name",
    "section_name",
    "roll_number",
    "admission_date",
    "leaving_date",
    "reason",
    "reason_details",
    "final_grade",
    "final_percentage",
    "attendance_percentage",
    "conduct",
    "issued_by",
    "verification_code",
    "student",
]


class TransferCertificateVerifyTests(TestCase):
    """Public verify endpoint: minimal payload, no PII, no oracle, throttled."""

    def setUp(self):
        self.school = School.objects.create(name="Northfield Academy")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")
        self.unit = AcademicUnit.objects.create(campus=self.campus, name="Lower")
        self.class_obj = Class.objects.create(unit=self.unit, name="Grade 6")
        self.section = Section.objects.create(class_obj=self.class_obj, name="A")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )
        self.guardian = Guardian.objects.create(
            name="Ada Parent", relationship="Mother", phone="555-4000"
        )
        self.student = Student.objects.create(
            institution=self.school,
            admission_number="ADM-001",
            first_name="Alan",
            last_name="Kid",
            gender="male",
            status="active",
            primary_campus=self.campus,
            guardian=self.guardian,
        )
        Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
            status="active",
        )
        self.admin = make_user("admin", Role.SUPER_ADMIN, self.school)

    def _make_certificate(self, status="draft"):
        certificate = TransferCertificate(
            institution=self.school,
            student=self.student,
            certificate_number=f"TC-{status.upper()}-0001",
            admission_number="ADM-001",
            full_name="Alan Kid",
            date_of_birth=date(2014, 3, 12),
            gender="male",
            guardian_name="Ada Parent",
            guardian_relationship="Mother",
            guardian_phone="555-4000",
            campus=self.campus,
            academic_year=self.year,
            class_obj=self.class_obj,
            section=self.section,
            admission_date=date(2022, 9, 1),
            leaving_date=date(2026, 7, 31),
            status=status,
        )
        certificate.save()
        return certificate

    def _issue(self, certificate):
        return certificate.issue(self.admin)

    def _verify(self, code):
        return APIClient().get(f"/api/students/transfer-certificates/verify/{code}/")

    def test_issued_certificate_returns_only_minimal_public_data(self):
        certificate = self._issue(self._make_certificate())
        response = self._verify(certificate.verification_code)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data.keys()), PUBLIC_FIELDS)
        self.assertEqual(data["certificate_number"], certificate.certificate_number)
        self.assertEqual(data["student_name"], "Alan Kid")
        self.assertEqual(data["campus"], "Main Campus")
        self.assertEqual(data["status"], "issued")
        for field in SENSITIVE_FIELDS:
            self.assertNotIn(field, data)

    def test_unknown_code_returns_404(self):
        response = self._verify("ZZZZZZZZ")

        self.assertEqual(response.status_code, 404)

    def test_cancelled_certificate_returns_404(self):
        certificate = self._issue(self._make_certificate())
        certificate.cancel(self.admin)

        response = self._verify(certificate.verification_code)

        self.assertEqual(response.status_code, 404)

    def test_draft_certificate_returns_404(self):
        certificate = self._make_certificate(status="draft")

        response = self._verify(certificate.verification_code)

        self.assertEqual(response.status_code, 404)

    def test_verification_code_matching_is_case_insensitive(self):
        certificate = self._issue(self._make_certificate())

        response = self._verify(certificate.verification_code.lower())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["certificate_number"], certificate.certificate_number)

    def test_verification_endpoint_is_throttled(self):
        certificate = self._issue(self._make_certificate())

        original_rates = ScopedRateThrottle.THROTTLE_RATES
        ScopedRateThrottle.THROTTLE_RATES = {
            "transfer_certificate_verify": "2/min",
        }
        try:
            with override_settings(
                CACHES={
                    "default": {
                        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                        "LOCATION": "transfer-certificate-verify-throttle-test",
                    }
                }
            ):
                client = APIClient()
                url = f"/api/students/transfer-certificates/verify/{certificate.verification_code}/"
                self.assertEqual(client.get(url).status_code, 200)
                self.assertEqual(client.get(url).status_code, 200)
                self.assertEqual(client.get(url).status_code, 429)
        finally:
            ScopedRateThrottle.THROTTLE_RATES = original_rates