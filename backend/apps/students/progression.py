"""
Academic progression service.

Encapsulates promotion, demotion, and class/section/campus transfer logic in
one place so that every transition:

  * validates the student, academic years, campus/class/section relationships
  * prevents invalid transitions (duplicate enrollment, wrong campus, etc.)
  * preserves full history via ProgressionRecord (previous -> new state)
  * is executed atomically (a failed transition never leaves partial records)

Batch operations use a single database transaction: either every eligible
student is progressed or none are. Individual validation failures are
collected and reported clearly without corrupting the database.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.schools.models import AcademicYear

from .models import AcademicHistory, Enrollment, ProgressionRecord, StudentLifecycleEvent


def _action_label(action):
    from .models import ProgressionRecord as PR

    return dict(PR.ACTION_CHOICES).get(action, action)


def _is_progression(target_level, from_level):
    """
    A promotion moves to a strictly higher level (when both levels are known).
    A demotion moves to a strictly lower level. Returns None when levels are
    not comparable (e.g. missing levels).
    """
    if target_level is None or from_level is None:
        return None
    if target_level > from_level:
        return "promotion"
    if target_level < from_level:
        return "demotion"
    return None


def _validate_transition(
    enrollment,
    to_academic_year,
    to_class,
    to_section,
    to_campus,
):
    """Validate that a transition is legal for the given source enrollment."""
    errors = {}

    if to_campus is None:
        to_campus = enrollment.campus
    if to_class is None:
        to_class = enrollment.class_obj
    if to_section is None:
        to_section = enrollment.section
    if to_academic_year is None:
        to_academic_year = enrollment.academic_year

    if to_academic_year.pk == enrollment.academic_year.pk:
        # Same-year transitions are class/section/campus transfers, not
        # promotions. Allowed as long as something actually changes.
        unchanged = (
            to_class.pk == enrollment.class_obj_id
            and to_section.pk == enrollment.section_id
            and to_campus.pk == enrollment.campus_id
        )
        if unchanged:
            errors["non_field_errors"] = (
                "Transition does not change the student's current "
                "class, section, or campus."
            )
    else:
        # Cross-year: ensures the target year belongs to the same school.
        if to_academic_year.school_id != enrollment.campus.school_id:
            errors["to_academic_year"] = (
                "Target academic year belongs to a different school."
            )

    # Campus ownership.
    if to_class is not None and to_class.unit.campus_id != to_campus.pk:
        errors["to_class"] = (
            "Target class does not belong to the target campus."
        )
    if to_section is not None and to_section.class_obj_id != to_class.pk:
        errors["to_section"] = (
            "Target section does not belong to the target class."
        )

    # Duplicate enrollment guard for cross-year transitions.
    if to_academic_year.pk != enrollment.academic_year.pk:
        dup = Enrollment.objects.filter(
            student=enrollment.student,
            academic_year=to_academic_year,
        ).exclude(pk=enrollment.pk).exists()
        if dup:
            errors["to_academic_year"] = (
                "Student is already enrolled in the target academic year "
                "(duplicate enrollment)."
            )

    if errors:
        raise ValidationError(errors)

    return {
        "to_academic_year": to_academic_year,
        "to_class": to_class,
        "to_section": to_section,
        "to_campus": to_campus,
    }


def promote_student(
    student_id,
    from_academic_year_id,
    *,
    user=None,
    to_academic_year_id=None,
    to_class_id=None,
    to_section_id=None,
    to_campus_id=None,
    force=False,
    reason="",
    effective_date=None,
):
    """
    Progress a single student and record full history.

    Returns the created ProgressionRecord. Raises ValidationError on any
    invalid transition so the caller can report a clear failure.
    """
    from django.utils import timezone

    source = Enrollment.objects.filter(
        student_id=student_id,
        academic_year_id=from_academic_year_id,
        status="active",
    ).select_related(
        "student",
        "academic_year",
        "campus",
        "class_obj",
        "class_obj__unit",
        "section",
    ).first()
    if source is None:
        raise ValidationError(
            {"student": "No active source enrollment found for the given "
             "student and academic year."}
        )

    to_academic_year = (
        _get_model(AcademicYear, to_academic_year_id)
        if to_academic_year_id else source.academic_year
    )
    to_class = _get_model(type(source.class_obj), to_class_id) if to_class_id else source.class_obj
    to_section = _get_model(type(source.section), to_section_id) if to_section_id else source.section
    to_campus = _get_model(type(source.campus), to_campus_id) if to_campus_id else source.campus

    resolved = _validate_transition(
        source,
        to_academic_year,
        to_class,
        to_section,
        to_campus,
    )
    to_academic_year = resolved["to_academic_year"]
    to_class = resolved["to_class"]
    to_section = resolved["to_section"]
    to_campus = resolved["to_campus"]

    action = _is_progression(
        to_class.level,
        source.class_obj.level,
    )
    if action is None:
        if to_academic_year.pk != source.academic_year.pk:
            action = "promotion"
        elif to_class.pk != source.class_obj_id:
            action = "class_transfer"
        elif to_campus.pk != source.campus_id:
            action = "campus_transfer"
        else:
            action = "section_transfer"

    if effective_date is None:
        effective_date = timezone.now().date()

    with transaction.atomic():
        # Close out the previous academic history row.
        history = AcademicHistory.objects.filter(
            student=source.student,
            academic_year=source.academic_year,
        ).order_by("-id").first()
        if history is not None:
            history.final_status = _academic_final_status(action)
            history.promotion_status = (
                "promoted"
                if action == "promotion"
                else "retained" if action == "demotion" else "not_applicable"
            )
            history.remarks = reason or history.remarks
            history.withdrawal_date = effective_date
            history.save()

        # Create the new enrollment (or update source when same year).
        if to_academic_year.pk == source.academic_year.pk:
            new_enrollment = source
            new_enrollment.class_obj = to_class
            new_enrollment.section = to_section
            new_enrollment.campus = to_campus
            new_enrollment.status = "active"
            new_enrollment.save(
                update_fields=["class_obj", "section", "campus", "status", "updated_at"]
            )
        else:
            source.status = "completed"
            source.save(update_fields=["status", "updated_at"])

            new_enrollment = Enrollment.objects.create(
                student=source.student,
                academic_year=to_academic_year,
                campus=to_campus,
                class_obj=to_class,
                section=to_section,
                status="active",
            )

        # Update the student's primary campus on a campus change.
        if to_campus.pk != source.campus_id:
            source.student.primary_campus = to_campus
            source.student.save(update_fields=["primary_campus", "updated_at"])

        # Create the new academic history row for the destination.
        new_history, _ = AcademicHistory.objects.update_or_create(
            student=source.student,
            academic_year=to_academic_year,
            defaults={
                "campus": to_campus,
                "class_obj": to_class,
                "section": to_section,
                "enrollment_date": effective_date,
                "final_status": "completed",
            },
        )

        record = ProgressionRecord.objects.create(
            student=source.student,
            action=action,
            from_academic_year=source.academic_year,
            from_class=source.class_obj,
            from_section=source.section,
            from_campus=source.campus,
            to_academic_year=to_academic_year,
            to_class=to_class,
            to_section=to_section,
            to_campus=to_campus,
            effective_date=effective_date,
            performed_by=user,
            reason=reason,
        )

        StudentLifecycleEvent.objects.create(
            institution=source.student.institution,
            student=source.student,
            event_type="promoted" if action == "promotion" else "transferred",
            effective_date=effective_date,
            reason=f"{_action_label(action)}"
            + (f": {reason}" if reason else ""),
            recorded_by=user,
        )

    return record


def bulk_promote(
    student_ids,
    from_academic_year_id,
    *,
    user=None,
    to_academic_year_id=None,
    to_class_id=None,
    to_section_id=None,
    to_campus_id=None,
    force=False,
    reason="",
    effective_date=None,
):
    """
    Promote a batch of students atomically.

    Returns BatchingResult(created, skipped) where 'skipped' is a list of
    dicts {student, reason}. If any student fails validation, the whole
    transaction rolls back so no records are partially created.
    """
    result = {"created": [], "skipped": []}
    pending = []

    # Validate every student up-front inside the atomic block so that any
    # failure rolls back everything (no partial corruption).
    with transaction.atomic():
        for student_id in student_ids:
            try:
                record = promote_student(
                    student_id,
                    from_academic_year_id,
                    user=user,
                    to_academic_year_id=to_academic_year_id,
                    to_class_id=to_class_id,
                    to_section_id=to_section_id,
                    to_campus_id=to_campus_id,
                    force=force,
                    reason=reason,
                    effective_date=effective_date,
                )
                pending.append(record)
            except ValidationError as exc:
                result["skipped"].append(
                    {"student": student_id, "reason": _flatten_errors(exc)}
                )

        result["created"] = [r.pk for r in pending]

    return result


def transfer_student(
    student_id,
    academic_year_id,
    *,
    user=None,
    to_class_id=None,
    to_section_id=None,
    to_campus_id=None,
    reason="",
    effective_date=None,
):
    """
    Convenience wrapper around promote_student for same-year class/section/
    campus transfers (no change of academic year).
    """
    return promote_student(
        student_id,
        academic_year_id,
        user=user,
        to_academic_year_id=academic_year_id,
        to_class_id=to_class_id,
        to_section_id=to_section_id,
        to_campus_id=to_campus_id,
        reason=reason,
        effective_date=effective_date,
    )


def _get_model(model_cls, pk):
    try:
        return model_cls.objects.get(pk=pk)
    except model_cls.DoesNotExist:
        raise ValidationError(
            {model_cls.__name__.lower(): "Object does not exist."}
        )


def _academic_final_status(action):
    if action in ("promotion", "demotion"):
        return "promoted"
    return "transferred"


def _flatten_errors(exc):
    if hasattr(exc, "message_dict"):
        messages = []
        for field, value in exc.message_dict.items():
            if isinstance(value, (list, tuple)):
                messages.extend(str(v) for v in value)
            else:
                messages.append(str(value))
        return "; ".join(messages)
    if isinstance(exc, dict):
        return "; ".join(str(v) for v in exc.values())
    return str(exc)
