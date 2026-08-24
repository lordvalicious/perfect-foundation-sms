"""Shared helpers for report generation."""

from decimal import Decimal

from django.http import HttpResponse


def to_csv(filename, headers, rows):
    """Build an ``HttpResponse`` containing CSV data."""
    import csv

    response = HttpResponse(
        content_type="text/csv; charset=utf-8",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    response.write("\ufeff")

    writer = csv.writer(response)

    writer.writerow(headers)
    writer.writerows(rows)

    return response


def quantize(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def prefetch_reportcard_results(cards):
    """Bulk-load StudentResults for many report cards in one query.

    ReportCard.results normally runs one query per card (N+1). This
    pre-populates the per-instance ``_cached_results`` cache that the
    property checks first, so loops over many cards stay fast.
    """
    from apps.exams.models import StudentResult

    cards = list(cards)

    if not cards:
        return cards

    pairs = {(card.exam_id, card.student_id) for card in cards}
    exam_ids = {exam_id for exam_id, _ in pairs}

    grouped = {}

    for result in (
        StudentResult.objects
        .filter(exam_id__in=exam_ids)
        .select_related("exam_subject__subject")
        .order_by("exam_subject__subject__name")
    ):
        key = (result.exam_id, result.student_id)

        if key in pairs:
            grouped.setdefault(key, []).append(result)

    for card in cards:
        card._cached_results = grouped.get(
            (card.exam_id, card.student_id),
            [],
        )

    return cards
