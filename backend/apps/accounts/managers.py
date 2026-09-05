"""Tenant-aware managers and mixins for multi-tenant isolation.

Every model that belongs to an institution should use TenantManagerMixin
to automatically filter querysets by the current request's institution.

Usage:
    from apps.accounts.managers import TenantManagerMixin

    class MyModel(models.Model):
        institution = models.ForeignKey('schools.School', ...)
        objects = TenantManagerMixin().get_manager()
"""

from contextvars import ContextVar
from django.db import models


class TenantManager(models.Manager):
    """Manager that filters querysets by institution from contextvar request.

    The active institution is set by middleware via contextvars.
    Models using this manager automatically scope all queries to the current
    tenant unless .all_tenants() is called.
    """

    _auto_filter = True

    def get_queryset(self):
        qs = super().get_queryset()
        if self._auto_filter:
            institution = get_current_institution()
            if institution is not None:
                qs = qs.filter(institution=institution)
        return qs

    def all_tenants(self):
        """Return unfiltered queryset (bypasses tenant scoping)."""
        return super().get_queryset()

    def for_institution(self, institution):
        """Return queryset explicitly filtered to a specific institution."""
        return super().get_queryset().filter(institution=institution)


class TenantManagerMixin:
    """Mixin to add a tenant-scoped manager to a model.

    Use as:  objects = TenantManagerMixin().get_manager()
    """

    def get_manager(self):
        return TenantManager


# ---------------------------------------------------------------------------
# Contextvar storage for the current request / institution (async-safe)
# ---------------------------------------------------------------------------

_current_institution: ContextVar | None = ContextVar("_current_institution", default=None)
_current_request: ContextVar | None = ContextVar("_current_request", default=None)


def set_current_institution(institution):
    """Set the current institution for this context (called by middleware)."""
    _current_institution.set(institution)


def get_current_institution():
    """Get the current institution for this context."""
    return _current_institution.get()


def clear_current_institution():
    """Clear the current institution (called at end of request)."""
    _current_institution.set(None)


def set_current_request(request):
    """Set the current request for this context."""
    _current_request.set(request)


def get_current_request():
    """Get the current request for this context."""
    return _current_request.get()


def clear_current_request():
    """Clear the current request (called at end of request)."""
    _current_request.set(None)


# =============================================================================
# Campus-scoped Manager
# =============================================================================

class CampusScopedManager(models.Manager):
    """
    Manager that filters querysets by campus from the current request.
    
    Uses the campus isolation logic from apps.accounts.access to automatically
    scope queries to the user's allowed campuses.
    
    Usage:
        class MyModel(models.Model):
            campus = models.ForeignKey('schools.Campus', ...)
            objects = CampusScopedManager()
            
    For models with nested campus relations, specify the campus_field:
        class MyModel(models.Model):
            class_obj = models.ForeignKey('schools.Class', ...)
            objects = CampusScopedManager(campus_field="class_obj__unit__campus_id")
    """
    
    def __init__(self, campus_field="campus_id", institution_field="institution_id"):
        super().__init__()
        self.campus_field = campus_field
        self.institution_field = institution_field
    
    def get_queryset(self):
        from apps.accounts.access import apply_campus_scope
        from apps.accounts.managers import get_current_request
        
        qs = super().get_queryset()
        request = get_current_request()
        
        if request is not None:
            qs = apply_campus_scope(
                qs, 
                request, 
                campus_field=self.campus_field,
                institution_field=self.institution_field,
            )
        
        return qs
    
    def all_campuses(self):
        """Return unfiltered queryset (bypasses campus scoping)."""
        return super().get_queryset()
    
    def for_campus(self, campus_id):
        """Return queryset explicitly filtered to a specific campus."""
        return super().get_queryset().filter(**{self.campus_field: campus_id})


class CampusScopedManagerMixin:
    """Mixin to add a campus-scoped manager to a model."""
    
    def __init__(self, campus_field="campus_id", institution_field="institution_id"):
        self.campus_field = campus_field
        self.institution_field = institution_field
    
    def get_manager(self):
        return CampusScopedManager(
            campus_field=self.campus_field,
            institution_field=self.institution_field,
        )
