from django.urls import path

from .branding_views import SchoolBrandingView
from .platform_views import (
    CurrentModulesView,
    TenantDetailView,
    TenantListCreateView,
)
from .tenant_views import PublicTenantConfigView
from .views import (
    AcademicUnitListView,
    AcademicYearListView,
    CampusViewSet,
    ClassListView,
    SchoolViewSet,
    SectionListView,
    SubjectListView,
    SubjectOfferingListView,
    TermListView,
)

urlpatterns = [
    path("", SchoolViewSet.as_view({"get": "list"}), name="school-list"),
    path("<int:pk>/pause/", SchoolViewSet.as_view({"post": "pause"}), name="school-pause"),
    path("<int:pk>/activate/", SchoolViewSet.as_view({"post": "activate"}), name="school-activate"),
    path("<int:pk>/archive/", SchoolViewSet.as_view({"post": "archive"}), name="school-archive"),
    path("<int:pk>/unarchive/", SchoolViewSet.as_view({"post": "unarchive"}), name="school-unarchive"),
    path("campuses/", CampusViewSet.as_view({"get": "list", "post": "create"}), name="campus-list"),
    path(
        "campuses/<int:pk>/",
        CampusViewSet.as_view({
            "get": "retrieve",
            "patch": "partial_update",
            "put": "update",
            "delete": "destroy",
        }),
        name="campus-detail",
    ),
    path("units/", AcademicUnitListView.as_view(), name="academic-unit-list"),
    path("classes/", ClassListView.as_view(), name="class-list"),
    path("sections/", SectionListView.as_view(), name="section-list"),
    path("academic-years/", AcademicYearListView.as_view(), name="academic-year-list"),
    path("terms/", TermListView.as_view(), name="term-list"),
    path("subjects/", SubjectListView.as_view(), name="subject-list"),
    path("offerings/", SubjectOfferingListView.as_view(), name="subject-offering-list"),
    path("branding/", SchoolBrandingView.as_view(), name="school-branding"),
    path("tenant-config/", PublicTenantConfigView.as_view(), name="public-tenant-config"),
    path("modules/current/", CurrentModulesView.as_view(), name="current-modules"),
    path("tenants/", TenantListCreateView.as_view(), name="tenant-list"),
    path("tenants/<int:pk>/", TenantDetailView.as_view(), name="tenant-detail"),
]
