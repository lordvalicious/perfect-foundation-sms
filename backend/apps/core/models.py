"""Base model mixins for the ERP system."""

from django.db import models
from django.utils import timezone


class SoftDeleteMixin(models.Model):
    """
    Mixin to add soft delete capability to models.

    When deleted, records are marked with deleted_at timestamp instead of
    being removed from the database. Queries should use the manager to
    automatically filter out deleted records.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_deleted",
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, user=None, hard=False):
        """Soft delete the object by setting deleted_at timestamp."""
        if hard:
            # Actually delete from database
            super().delete(using=using, keep_parents=keep_parents)
        else:
            self.deleted_at = timezone.now()
            self.deleted_by = user
            self.save(update_fields=["deleted_at", "deleted_by", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object from database."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted object."""
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by", "updated_at"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class SoftDeleteManager(models.Manager):
    """Manager that automatically filters out soft-deleted records."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def all_with_deleted(self):
        """Return queryset including soft-deleted records."""
        return super().get_queryset()

    def deleted_only(self):
        """Return only soft-deleted records."""
        return super().get_queryset().filter(deleted_at__isnull=False)


class TimeStampedMixin(models.Model):
    """Mixin to add created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CampusScopedMixin(models.Model):
    """Mixin to add campus foreign key with proper indexing."""

    campus = models.ForeignKey(
        "schools.Campus",
        on_delete=models.PROTECT,
        related_name="%(class)s_campus",
    )

    class Meta:
        abstract = True


class InstitutionScopedMixin(models.Model):
    """Mixin to add institution foreign key with proper indexing."""

    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="%(class)s_institution",
    )

    class Meta:
        abstract = True


class AuditableMixin(SoftDeleteMixin, TimeStampedMixin):
    """Combined mixin for audit fields and soft delete."""

    class Meta:
        abstract = True