"""Tenant-aware managers and mixins for multi-tenant isolation.

Every model that belongs to an institution should use TenantManagerMixin
to automatically filter querysets by the current request's institution.

Usage:
    from apps.accounts.managers import TenantManagerMixin

    class MyModel(models.Model):
        institution = models.ForeignKey('schools.School', ...)
        objects = TenantManagerMixin().get_manager()
"""

from django.db import models


class TenantManager(models.Manager):
    """Manager that filters querysets by institution from thread-local request.

    The active institution is set by TenantMiddleware via thread-local storage.
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
# Thread-local storage for the current request / institution
# ---------------------------------------------------------------------------

import threading

_thread_locals = threading.local()


def set_current_institution(institution):
    """Set the current institution for this thread (called by middleware)."""
    _thread_locals._current_institution = institution


def get_current_institution():
    """Get the current institution for this thread."""
    return getattr(_thread_locals, "_current_institution", None)


def clear_current_institution():
    """Clear the current institution (called at end of request)."""
    _thread_locals._current_institution = None


def set_current_request(request):
    """Set the current request for this thread."""
    _thread_locals._current_request = request


def get_current_request():
    """Get the current request for this thread."""
    return getattr(_thread_locals, "_current_request", None)


def clear_current_request():
    """Clear the current request (called at end of request)."""
    _thread_locals._current_request = None
