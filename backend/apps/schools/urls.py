from django.urls import path

from .branding_views import SchoolBrandingView
from .tenant_views import PublicTenantConfigView
from .views import (
    AcademicUnitListView,
    AcademicYearListView,
    CampusListView,
    ClassListView,
    SchoolListView,
    SectionListView,
    SubjectListView,
    SubjectOfferingListView,
    TermListView,
)


urlpatterns = [
    path("schools/", SchoolListView.as_view(), name="school-list"),
    path("campuses/", CampusListView.as_view(), name="campus-list"),
    path("units/", AcademicUnitListView.as_view(), name="academic-unit-list"),
    path("classes/", ClassListView.as_view(), name="class-list"),
    path("sections/", SectionListView.as_view(), name="section-list"),
    path("academic-years/", AcademicYearListView.as_view(), name="academic-year-list"),
    path("terms/", TermListView.as_view(), name="term-list"),
    path("subjects/", SubjectListView.as_view(), name="subject-list"),
    path("offerings/", SubjectOfferingListView.as_view(), name="subject-offering-list"),
    path("branding/", SchoolBrandingView.as_view(), name="school-branding"),
    path("tenant-config/", PublicTenantConfigView.as_view(), name="public-tenant-config"),
]
