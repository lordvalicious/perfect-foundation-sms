"""Composite at-risk report: attendance x fees x discipline."""

from decimal import Decimal

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope

from .utils import quantize, to_csv


class AtRiskReportView(APIView):
    """GET /api/reports/at-risk/?attendance_threshold=75&days=30&points=3

    Merges three early-warning signals per student:

    - attendance rate over a rolling window below ``attendance_threshold``
    - any outstanding invoice balance
    - cumulative discipline points (>= ``points`` scores higher)

    Composite score -> risk level: high / medium / watch.
    """

    permission_classes = [IsAuthenticated]

    def _data(self, request):
        try:
            att_threshold = float(request.query_params.get(
                "attendance_threshold", 75))
        except (TypeError, ValueError):
            att_threshold = 75.0

        try:
            points_major = int(request.query_params.get("points", 3))
        except (TypeError, ValueError):
            points_major = 3

        try:
            days = max(7, min(int(request.query_params.get("days", 30)), 180))
        except (TypeError, ValueError):
            days = 30

        today = timezone.localdate()
        window_start = today - timezone.timedelta(days=days)

        students = {}

        def entry(student, campus_name="", class_name=""):
            key = student.id if hasattr(student, "id") else student

            return students.setdefault(key, {
                "name": getattr(student, "full_name", ""),
                "admission_number": getattr(
                    student, "admission_number", ""),
                "campus": campus_name,
                "class": class_name,
                "attendance_days": 0,
                "attended": 0,
                "attendance_rate": None,
                "outstanding": Decimal("0"),
                "open_invoices": 0,
                "discipline_points": 0,
                "incidents": 0,
                "_signals": [],
            })

        # --- Signal 1: attendance over the rolling window ---
        from apps.attendance.models import Attendance

        records = (
            Attendance.objects
            .filter(date__gte=window_start, date__lte=today)
            .select_related("student", "campus", "class_obj")
        )

        records = apply_campus_scope(records, request)

        for record in records.iterator():
            item = entry(record.student, record.campus.name,
                         record.class_obj.name)
            item["attendance_days"] += 1

            if record.status in ("present", "late"):
                item["attended"] += 1

        # --- Signal 2: outstanding fees ---
        from apps.finance.models import Invoice

        invoices = (
            Invoice.objects
            .filter(status__in=["issued", "partial", "overdue"])
            .prefetch_related(
                "items",
                "payments",
                "payments__refunds",
                "payments__reversals",
                "concessions",
            )
            .select_related("student", "enrollment__campus",
                            "enrollment__class_obj")
        )

        invoices = apply_campus_scope(
            invoices, request, "enrollment__campus_id")

        for invoice in invoices:
            balance = invoice.balance

            if balance <= 0:
                continue

            item = entry(
                invoice.student,
                invoice.enrollment.campus.name
                if invoice.enrollment.campus_id else "-",
                invoice.enrollment.class_obj.name
                if invoice.enrollment.class_obj_id else "-",
            )

            item["outstanding"] += balance
            item["open_invoices"] += 1

        # --- Signal 3: discipline ---
        from apps.discipline.models import Incident

        incidents = (
            Incident.objects
            .all()
            .select_related("student", "campus")
        )

        incidents = apply_campus_scope(incidents, request)

        for incident in incidents:
            item = entry(
                incident.student,
                incident.campus.name if incident.campus_id else "-",
            )

            item["discipline_points"] += incident.points or 0
            item["incidents"] += 1

        # --- Score & level ---
        rows = []

        for student_id, item in students.items():
            days_tracked = item.pop("attendance_days")

            if days_tracked:
                rate = round(item["attended"] / days_tracked * 100, 1)
                item["attendance_rate"] = rate

            score = 0
            signals = []

            low_attendance = (
                item["attendance_rate"] is not None
                and item["attendance_rate"] < att_threshold
            )

            if low_attendance:
                score += 2
                signals.append("low_attendance")

            if item["outstanding"] > 0:
                score += 1
                signals.append("fee_dues")

            if item["discipline_points"] >= points_major:
                score += 2
                signals.append("discipline")
            elif item["discipline_points"] > 0:
                score += 1
                signals.append("minor_discipline")

            item["score"] = score
            item["signals"] = signals
            item["risk_level"] = (
                "high" if score >= 4 else
                "medium" if score >= 2 else ""
            )

            if score < 2:
                continue

            rows.append({
                "id": student_id,
                "name": item["name"],
                "admission_number": item["admission_number"],
                "campus": item["campus"],
                "class": item["class"],
                "attendance_rate": item["attendance_rate"],
                "attendance_days": days_tracked,
                "outstanding": quantize(item["outstanding"]),
                "open_invoices": item["open_invoices"],
                "discipline_points": item["discipline_points"],
                "incidents": item["incidents"],
                "score": score,
                "signals": signals,
                "risk_level": item["risk_level"],
            })

        rows.sort(
            key=lambda row: (-row["score"], row["attendance_rate"]
                             if row["attendance_rate"] is not None else 100),
        )

        try:
            limit = int(request.query_params.get("limit", 200))
        except (TypeError, ValueError):
            limit = 200

        rows = rows[:limit] if limit else rows

        levels = {"high": 0, "medium": 0}

        for row in rows:
            if row["risk_level"] in levels:
                levels[row["risk_level"]] += 1

        return {
            "summary": {
                "attendance_threshold": att_threshold,
                "window_days": days,
                "discipline_points_threshold": points_major,
                "tracked": len(rows),
                "high": levels["high"],
                "medium": levels["medium"],
            },
            "students": rows,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "at_risk_report.csv",
            ["Student", "Admission No", "Campus", "Class",
             "Attendance %", "Outstanding", "Discipline Points",
             "Signals", "Risk Level"],
            [
                [
                    row["name"],
                    row["admission_number"],
                    row["campus"],
                    row["class"],
                    (f"{row['attendance_rate']}%"
                     if row["attendance_rate"] is not None else "-"),
                    row["outstanding"],
                    row["discipline_points"],
                    ", ".join(row["signals"]),
                    row["risk_level"],
                ]
                for row in data["students"]
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request, response, *args, **kwargs)
