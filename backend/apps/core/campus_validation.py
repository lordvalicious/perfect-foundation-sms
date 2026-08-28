"""Campus validation mixins for models.

These mixins can be added to models to enforce campus-level validation
at the model layer, ensuring data integrity even when bypassing API validation.
"""

from django.core.exceptions import ValidationError
from django.db import models


class CampusValidationMixin:
    """
    Mixin to add campus validation to models that have a campus field.
    
    Subclasses must define:
    - campus_field: The field name for the campus FK (default: "campus")
    - institution_field: The field name for the institution FK (default: "institution")
    
    And implement:
    - get_campus(): Return the campus instance
    - get_institution(): Return the institution instance
    """
    
    campus_field = "campus"
    institution_field = "institution"
    
    def clean(self):
        super().clean() if hasattr(super(), 'clean') else None
        self._validate_campus_institution_consistency()
    
    def _validate_campus_institution_consistency(self):
        """Ensure campus belongs to the same institution as the record."""
        campus = getattr(self, self.campus_field, None)
        institution = getattr(self, self.institution_field, None)
        
        if campus and institution:
            if campus.school_id != institution.id:
                raise ValidationError({
                    self.campus_field: (
                        f"The selected campus does not belong to the "
                        f"selected institution ({institution.name})."
                    )
                })
    
    def save(self, *args, **kwargs):
        # Only run full_clean if not already validated
        # This ensures validation runs on direct model saves too
        if not kwargs.get('_skip_validation', False):
            self.full_clean()
        return super().save(*args, **kwargs)


class NestedCampusValidationMixin:
    """
    Mixin for models that don't have a direct campus field but have
    a nested relationship to campus (e.g., through class -> unit -> campus).
    
    Subclasses must implement get_campus() and get_institution().
    """
    
    campus_path = None  # e.g., "class_obj__unit__campus"
    institution_path = None  # e.g., "academic_year__school"
    
    def clean(self):
        super().clean() if hasattr(super(), 'clean') else None
        self._validate_nested_campus_institution()
    
    def _validate_nested_campus_institution(self):
        """Validate nested campus belongs to the same institution."""
        campus = self._get_related_object(self.campus_path)
        institution = self._get_related_object(self.institution_path)
        
        if campus and institution:
            if campus.school_id != institution.id:
                raise ValidationError({
                    self.campus_path: (
                        f"The selected campus does not belong to the "
                        f"selected institution ({institution.name})."
                    )
                })
    
    def _get_related_object(self, path):
        """Traverse a relationship path to get the related object."""
        if not path:
            return None
        
        obj = self
        for part in path.split("__"):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj


class CampusAssignmentValidationMixin:
    """
    Mixin for models that link entities to campuses (e.g., TeacherAssignment,
    Enrollment). Validates that all related entities belong to the same campus.
    """
    
    # Override in subclass with the field names
    campus_field = "campus"
    related_fields = []  # List of field names that must match the campus
    
    def clean(self):
        super().clean() if hasattr(super(), 'clean') else None
        self._validate_campus_assignments()
    
    def _validate_campus_assignments(self):
        campus = getattr(self, self.campus_field, None)
        if not campus:
            return
        
        for field_name in self.related_fields:
            related_obj = getattr(self, field_name, None)
            if related_obj is None:
                continue
            
            # Get the campus from the related object
            related_campus = self._get_campus_from_object(related_obj)
            if related_campus and related_campus.id != campus.id:
                raise ValidationError({
                    field_name: (
                        f"The selected {field_name} does not belong to "
                        f"the selected campus ({campus.name})."
                    )
                })
    
    def _get_campus_from_object(self, obj):
        """Extract campus from various object types."""
        # Direct campus FK
        if hasattr(obj, 'campus') and obj.campus:
            return obj.campus
        # Primary campus
        if hasattr(obj, 'primary_campus') and obj.primary_campus:
            return obj.primary_campus
        # Class -> Unit -> Campus
        if hasattr(obj, 'unit') and obj.unit and hasattr(obj.unit, 'campus'):
            return obj.unit.campus
        # Section -> Class -> Unit -> Campus
        if hasattr(obj, 'class_obj') and obj.class_obj:
            return self._get_campus_from_object(obj.class_obj)
        # AcademicYear -> School (not campus)
        # Enrollment has campus directly
        if hasattr(obj, 'campus_id'):
            from apps.schools.models import Campus
            try:
                return Campus.objects.get(pk=obj.campus_id)
            except Campus.DoesNotExist:
                return None
        return None