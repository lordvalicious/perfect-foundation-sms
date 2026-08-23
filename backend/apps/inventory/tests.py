from django.test import TestCase

from apps.accounts.models import Role, StaffProfile
from apps.accounts.test_access import make_request, make_user
from apps.inventory.models import Asset
from apps.inventory.views import AssetListView
from apps.schools.models import Campus, School


class AssetCampusIsolationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Inventory School")
        self.campus_a = Campus.objects.create(school=self.school, name="Campus A")
        self.campus_b = Campus.objects.create(school=self.school, name="Campus B")
        self.user = make_user("inventory-admin", Role.CAMPUS_ADMIN, self.school)
        StaffProfile.objects.create(
            user=self.user,
            employee_number="INV-001",
            first_name="Inventory",
            last_name="Admin",
            gender="male",
            primary_campus=self.campus_a,
        )

    def test_asset_list_includes_own_and_school_wide_assets_only(self):
        own = Asset.objects.create(name="Campus A asset", campus=self.campus_a)
        Asset.objects.create(name="Campus B asset", campus=self.campus_b)
        school_wide = Asset.objects.create(name="Shared asset")

        request = make_request(self.user)
        request.institution = self.school
        view = AssetListView()
        view.request = request

        self.assertQuerySetEqual(
            view.get_queryset().order_by("pk"),
            [own, school_wide],
            transform=lambda asset: asset,
        )