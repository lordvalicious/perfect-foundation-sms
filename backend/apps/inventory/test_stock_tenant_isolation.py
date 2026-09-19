"""Phase 8 F4 — Inventory stock movements enforce tenant ownership.

Regression: StockMovementListView.create looked up the asset and destination
campus unscoped, and stock.apply_movement did not verify that the asset,
source campus, destination campus, and resolved institution belong to one
tenant. A caller could move an institution-B asset or point a movement at an
institution-B campus.
"""

from django.test import TestCase
from rest_framework import status

from apps.accounts.models import Role, StaffProfile
from apps.accounts.test_access import make_user
from apps.inventory import stock
from apps.inventory.models import Asset, StockLevel, StockMovement
from apps.schools.models import Campus, School

MOVEMENTS_URL = "/api/inventory/stock/movements/"


class StockMovementTenantIsolationTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name="School A")
        self.school_b = School.objects.create(name="School B")
        self.campus_a1 = Campus.objects.create(school=self.school_a, name="Campus A1")
        self.campus_a2 = Campus.objects.create(school=self.school_a, name="Campus A2")
        self.campus_b1 = Campus.objects.create(school=self.school_b, name="Campus B1")

        self.asset_a = Asset.objects.create(
            name="Ink A",
            institution=self.school_a,
            campus=self.campus_a1,
            unit="box",
        )
        self.asset_b = Asset.objects.create(
            name="Ink B",
            institution=self.school_b,
            campus=self.campus_b1,
            unit="box",
        )

        self.admin_a = make_user("admin-a", Role.ADMIN, self.school_a)

        self.accountant_a = make_user("acc-a", Role.ACCOUNTANT, self.school_a)
        StaffProfile.objects.create(
            user=self.accountant_a,
            employee_number="ACC-A-001",
            first_name="Acc",
            last_name="A",
            gender="female",
            primary_campus=self.campus_a1,
        )

        self.client.login(username=self.admin_a.username, password="TestPass123!")

    def _post(self, payload):
        return self.client.post(MOVEMENTS_URL, payload, format="json")

    # The asset itself must belong to the active institution.
    def test_admin_a_cannot_move_school_b_asset(self):
        response = self._post(
            {
                "asset": self.asset_b.pk,
                "campus": self.campus_a1.pk,
                "movement_type": "receive",
                "quantity": 1,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accountant_a_cannot_move_school_b_asset(self):
        self.client.login(username=self.accountant_a.username, password="TestPass123!")
        response = self._post(
            {
                "asset": self.asset_b.pk,
                "campus": self.campus_a1.pk,
                "movement_type": "receive",
                "quantity": 1,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # The manager against which the asset was acquired belongs to tenant A.
    def test_admin_a_cannot_make_a_movement_at_school_b_campus(self):
        response = self._post(
            {
                "asset": self.asset_a.pk,
                "campus": self.campus_b1.pk,
                "movement_type": "receive",
                "quantity": 1,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Cross-tenant destination campus is rejected with no state mutation.
    def test_cross_tenant_destination_is_rejected_and_state_preserved(self):
        stock.apply_movement(
            asset=self.asset_a,
            campus=self.campus_a1,
            movement_type="receive",
            quantity=5,
            institution=self.school_a,
        )

        response = self._post(
            {
                "asset": self.asset_a.pk,
                "campus": self.campus_a1.pk,
                "destination_campus": self.campus_b1.pk,
                "movement_type": "transfer_out",
                "quantity": 2,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(
            StockMovement.objects.filter(movement_type="transfer_out").exists()
        )
        self.assertFalse(
            StockMovement.objects.filter(movement_type="transfer_in").exists()
        )
        self.asset_a.refresh_from_db()
        self.assertEqual(self.asset_a.quantity, 5)

    # Same-institution cross-campus transfers keep working.
    def test_same_institution_transfer_still_works(self):
        stock.apply_movement(
            asset=self.asset_a,
            campus=self.campus_a1,
            movement_type="receive",
            quantity=5,
            institution=self.school_a,
        )

        response = self._post(
            {
                "asset": self.asset_a.pk,
                "campus": self.campus_a1.pk,
                "destination_campus": self.campus_a2.pk,
                "movement_type": "transfer_out",
                "quantity": 2,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        level_a1 = StockLevel.objects.get(campus=self.campus_a1, asset=self.asset_a)
        level_a2 = StockLevel.objects.get(campus=self.campus_a2, asset=self.asset_a)
        self.assertEqual(level_a1.quantity, 3)
        self.assertEqual(level_a2.quantity, 2)

    # Engine-level defense, independent of the view.
    def test_engine_rejects_cross_tenant_destination(self):
        with self.assertRaises(stock.StockError):
            stock.apply_movement(
                asset=self.asset_a,
                campus=self.campus_a1,
                movement_type="receive",
                quantity=1,
                institution=self.school_a,
                destination_campus=self.campus_b1,
            )
        self.assertFalse(StockMovement.objects.exists())
        self.assertFalse(StockLevel.objects.exists())

    def test_engine_rejects_cross_tenant_institution_param(self):
        with self.assertRaises(stock.StockError):
            stock.apply_movement(
                asset=self.asset_a,
                campus=self.campus_a1,
                movement_type="receive",
                quantity=1,
                institution=self.school_b,
            )
        self.assertFalse(StockMovement.objects.exists())
        self.assertFalse(StockLevel.objects.exists())