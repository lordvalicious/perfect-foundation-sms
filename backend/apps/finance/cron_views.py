"""Cron-triggered finance jobs.

Designed for Vercel Cron: scheduled GET requests arrive with an
``Authorization: Bearer $CRON_SECRET`` header. The same endpoint can
also be triggered manually by a signed-in admin.
"""

import os
from decimal import Decimal

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.access import is_global


def _cron_secret_valid(request):
    expected = os.environ.get("CRON_SECRET", "")

    if not expected:
        return False

    header = request.META.get("HTTP_AUTHORIZATION", "")

    return header == f"Bearer {expected}"


class LateFeeCronView(APIView):
    """GET /api/finance/cron/late-fees/

    Query params (optional, fall back to env defaults):
        percent      e.g. 2
        flat         e.g. 200
        grace_days   default LATE_FEE_GRACE_DAYS or 5
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (_cron_secret_valid(request) or is_global(request.user)):
            return JsonResponse(
                {"detail": "Unauthorized."}, status=401
            )

        from apps.finance.late_fee_service import apply_late_fees

        def _decimal(name, default=None):
            raw = request.query_params.get(name)

            if raw is None:
                raw = os.environ.get(
                    f"LATE_FEE_{name.upper()}", default
                )

            if raw in (None, ""):
                return None

            try:
                return Decimal(str(raw))
            except Exception:
                raise ValueError(f"Invalid {name}.")

        grace_raw = request.query_params.get("grace_days")

        if grace_raw is None:
            grace_raw = os.environ.get("LATE_FEE_GRACE_DAYS", "5")

        try:
            grace_days = int(grace_raw)
            percent = _decimal("percent")
            flat = _decimal("flat")
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)

        if percent is None and flat is None:
            return JsonResponse(
                {
                    "detail": (
                        "No fee configured. Pass ?percent=2 (or ?flat=200) "
                        "or set LATE_FEE_PERCENT / LATE_FEE_FLAT."
                    )
                },
                status=400,
            )

        try:
            summary = apply_late_fees(
                percent=(
                    Decimal(str(percent)) if percent is not None else None
                ),
                flat=Decimal(str(flat)) if flat is not None else None,
                grace_days=grace_days,
                dry_run=request.query_params.get("dry_run") == "1",
            )
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)

        return JsonResponse(summary)
