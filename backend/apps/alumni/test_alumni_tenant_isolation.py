"""Phase 8 F5 — Alumni writes enforce tenant/campus ownership.

Regression: AlumniProfileSerializer had no ownership validation, so a user in
institution A could create/update Alumni records pointing at institution-B
campuses or students, or pair a student with the wrong campus.
"""

from rest_framework import status

from apps.alumni.models import AlumniProfile
from apps.tests.test_tenant_isolation import TenantIsolationTestBase

ALUMNI_URL = "/api/alumni/"


class AlumniWriteTenantIsolationTest(TenantIsolationTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.alumni_a = AlumniProfile.objects.create(
            institution=cls.school_a,
            campus=cls.campus_a1,
            full_name="Alumni A",
            batch_year=2020,
        )

    def _post(self, payload):
        return self.client.post(ALUMNI_URL, payload, format="json")

    def _patch(self, alumni_id, payload):
        return self.client.patch(
            f"{ALUMNI_URL}{alumni_id}/", payload, format="json"
        )

    def test_admin_a_cannot_create_alumni_with_school_b_campus(self):
        self._login(self.admin_a)
        response = self._post(
            {
                "campus": self.campus_b1.pk,
                "full_name": "Foreign Campus",
                "batch_year": 2020,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_a_cannot_create_alumni_for_school_b_student(self):
        self._login(self.admin_a)
        response = self._post(
            {
                "student": self.student_b1.pk,
                "full_name": "Foreign Student",
                "batch_year": 2020,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_campus_student_mismatch_is_rejected(self):
        self._login(self.admin_a)
        response = self._post(
            {
                "student": self.student_a1.pk,
                "campus": self.campus_a2.pk,
                "full_name": "Mismatched",
                "batch_year": 2020,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_create_stamps_the_institution(self):
        self._login(self.admin_a)
        response = self._post(
            {
                "student": self.student_a1.pk,
                "campus": self.campus_a1.pk,
                "full_name": "Legit Alumni",
                "batch_year": 2020,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record = AlumniProfile.objects.get(pk=response.json()["id"])
        self.assertEqual(record.institution, self.school_a)
        self.assertEqual(record.campus, self.campus_a1)
        self.assertEqual(record.student, self.student_a1)

    def test_admin_a_cannot_patch_existing_alumni_to_school_b_campus(self):
        self._login(self.admin_a)
        response = self._patch(
            self.alumni_a.pk, {"campus": self.campus_b1.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_a_cannot_patch_existing_alumni_to_school_b_student(self):
        self._login(self.admin_a)
        response = self._patch(
            self.alumni_a.pk, {"student": self.student_b1.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_b_cannot_modify_school_a_alumni(self):
        self._login(self.admin_b)
        response = self._patch(
            self.alumni_a.pk, {"full_name": "Hijacked"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)