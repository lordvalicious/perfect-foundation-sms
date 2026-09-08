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


def _normalize_summary(value):
    """Normalize a summary field into ``[{label, value}]`` items.

    The legacy report views return summaries as dicts like
    ``{"total_students": 12}`` while the PDF/print renderers expect a list
    of ``{"label": str, "value": any}``.  Without this the table builders
    iterate dict-keys (strings) and crash with ``AttributeError``.
    """
    if isinstance(value, list):
        items = []
        for item in value:
            if not isinstance(item, dict):
                continue
            items.append({
                "label": str(item.get("label", item.get("name", "—"))),
                "value": item.get("value", item.get("count", "—")),
            })
        return items

    if isinstance(value, dict):
        return [
            {
                "label": str(key).replace("_", " ").title(),
                "value": item,
            }
            for key, item in value.items()
        ]

    return []


def _table_payload(data):
    """Extract ``(headers, rows)`` from an unshaped report payload.

    Uses an explicit ``headers``/``rows`` pair when present, otherwise
    falls back to the first list-of-dicts field (e.g. ``classes``,
    ``students``, ``routes``) and derives column order from the keys.
    """
    headers = data.get("headers")
    rows = data.get("rows")

    if isinstance(headers, list) and isinstance(rows, list) and headers and rows:
        return headers, rows

    for key, value in data.items():
        if key in ("summary", "headers", "rows", "filters_applied"):
            continue
        if isinstance(value, list) and value and isinstance(value[0], dict):
            seen = []
            for row in value:
                for cell_key in row:
                    if cell_key not in seen:
                        seen.append(cell_key)
            return seen, [
                [row.get(header, "") for header in seen]
                for row in value
            ]

    return [], []


def normalize_report_payload(data):
    """Normalize any report payload into the shape expected by the
    PDF/print renderers: ``{summary, headers, rows, filters_applied}``.
    """
    if not isinstance(data, dict):
        data = {}

    headers, rows = _table_payload(data)

    return {
        "summary": _normalize_summary(data.get("summary")),
        "headers": headers,
        "rows": rows,
        "filters_applied": data.get("filters_applied", {}),
    }


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
