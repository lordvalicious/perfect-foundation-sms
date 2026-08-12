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
