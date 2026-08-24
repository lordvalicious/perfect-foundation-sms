"""API endpoint to run the timetable generator (admins only)."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import is_global
from apps.schools.models import AcademicYear, Campus


class TimetableGenerateView(APIView):
    """POST /api/timetable/generate/

    Body:
        campus: int | str        (id or exact name)
        academic_year: int       (optional, default latest active)
        lessons_per_subject: int (optional, default 5)
        days: [str]              (optional)
        confirm: true            REQUIRED — generation replaces entries.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_global(request.user):
            return Response(
                {"detail": "Only administrators can generate timetables."},
                status=403,
            )

        if request.data.get("confirm") is not True:
            return Response(
                {
                    "detail": (
                        "Pass confirm:true — generation replaces the "
                        "existing timetable for the campus."
                    )
                },
                status=400,
            )

        from apps.timetable.generator import generate_timetable

        campus_raw = request.data.get("campus")

        if not campus_raw:
            return Response(
                {"detail": "campus is required."}, status=400
            )

        campus = None

        if str(campus_raw).isdigit():
            campus = Campus.objects.filter(pk=campus_raw).first()

        if campus is None:
            campus = Campus.objects.filter(
                name__iexact=str(campus_raw)
            ).first()

        if campus is None:
            return Response(
                {"detail": f"Campus '{campus_raw}' not found."}, status=404
            )

        year_id = request.data.get("academic_year")

        year = (
            AcademicYear.objects.filter(pk=year_id).first()
            if year_id
            else (
                AcademicYear.objects.filter(
                    school=campus.school, status="active"
                ).order_by("-start_date").first()
                or AcademicYear.objects.filter(
                    school=campus.school
                ).order_by("-start_date").first()
            )
        )

        if year is None:
            return Response(
                {"detail": "No academic year found for this school."},
                status=400,
            )

        try:
            lessons = max(1, min(int(request.data.get("lessons_per_subject", 5)), 20))
        except (TypeError, ValueError):
            lessons = 5

        days = request.data.get("days") or [
            "monday", "tuesday", "wednesday", "thursday", "friday",
        ]

        try:
            stats = generate_timetable(
                campus=campus,
                academic_year=year,
                lessons_per_subject=lessons,
                days=[str(day).lower() for day in days],
                replace=True,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        stats["campus"] = campus.name
        stats["academic_year"] = year.name

        return Response(stats)
