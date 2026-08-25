"""Class-subject gradebook: every student's performance across exams."""

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope


class ClassGradebookView(APIView):
    """GET /api/exams/gradebook/?class_obj=&subject=&academic_year=

    Returns an exam-by-student percentage matrix for one class-subject,
    with each student's running weighted average and band grade.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.exams.models import ExamSubject, StudentResult
        from apps.reportcards.models import GradeBand
        from apps.schools.models import AcademicYear, Class

        class_obj = get_object_or_404(Class, pk=request.query_params.get("class_obj"))

        year_id = request.query_params.get("academic_year")
        year = (
            AcademicYear.objects.filter(pk=year_id).first()
            if year_id
            else AcademicYear.objects.filter(
                school=class_obj.unit.campus.school_id, status="active"
            ).order_by("-start_date").first()
        )

        if year is None:
            return Response({"detail": "No academic year."}, status=400)

        try:
            subject_id = int(request.query_params.get("subject"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "subject is required."}, status=400
            )

        section_filter = request.query_params.get("section")

        exams_qs = apply_campus_scope(
            class_obj.exams.filter(academic_year=year),
            request,
            "campus_id",
            institution_field="campus__school_id",
        ).order_by("start_date", "id")

        exam_subjects = {
            es.exam_id: es
            for es in ExamSubject.objects.filter(
                exam__in=exams_qs,
                subject_id=subject_id,
            ).select_related("exam")
        }

        ordered_exams = [
            exam for exam in exams_qs if exam.id in exam_subjects
        ]

        results = (
            StudentResult.objects
            .filter(exam_subject__in=list(exam_subjects.values()))
            .exclude(is_absent=True)
            .select_related("exam_subject", "student")
        )

        students = {}

        for result in results:
            student = result.student
            entry = students.setdefault(
                student.id,
                {
                    "id": student.id,
                    "name": student.full_name,
                    "admission_number": student.admission_number,
                    "scores": {},
                },
            )

            maximum = result.exam_subject.maximum_marks

            if not maximum:
                continue

            entry["scores"][str(result.exam_subject.exam_id)] = {
                "obtained": float(result.obtained_marks),
                "maximum": float(maximum),
                "percentage": round(
                    float(result.obtained_marks) / float(maximum) * 100, 1
                ),
            }

        rows = []

        for entry in students.values():
            pcts = [
                score["percentage"]
                for score in entry["scores"].values()
            ]

            average = (
                round(sum(pcts) / len(pcts), 1) if pcts else None
            )

            band = (
                GradeBand.band_for_percentage(average)
                if average is not None
                else None
            )

            section_name = ""

            rows.append({
                **entry,
                "average_percentage": average,
                "grade": band.letter_grade if band else "",
                "exams_taken": len(pcts),
            })

        if section_filter:
            rows = [r for r in rows if str(r.get("section")) == section_filter]

        rows.sort(key=lambda r: -(r["average_percentage"] or 0))

        return Response({
            "class": class_obj.name,
            "academic_year": year.name,
            "exams": [
                {"id": exam.id, "name": exam.name}
                for exam in ordered_exams
            ],
            "students": rows,
        })
