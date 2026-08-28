"""Examination and Result Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class ExamScheduleReportView(AggregateReportView):
    """Exam schedule report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "exam_schedule"
    model = "apps.exams.models.Exam"

    def get_base_queryset(self, request):
        from apps.exams.models import Exam
        return Exam.objects.select_related(
            "campus", "class_obj", "academic_year"
        ).prefetch_related("exam_subjects__subject")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        campus = request.query_params.get("campus")
        if campus:
            queryset = queryset.filter(campus_id=campus)

        class_obj = request.query_params.get("class")
        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_status = queryset.values("status").annotate(count=Count("id"))
        by_type = queryset.values("exam_type").annotate(count=Count("id"))
        by_campus = queryset.values("campus__name").annotate(count=Count("id"))

        return {
            "total_exams": total,
            "by_status": list(by_status),
            "by_type": list(by_type),
            "by_campus": list(by_campus),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for exam in queryset:
            subjects = exam.exam_subjects.all()
            rows.append({
                "name": exam.name,
                "type": exam.get_exam_type_display(),
                "campus": exam.campus.name,
                "class": exam.class_obj.name,
                "academic_year": exam.academic_year.name,
                "start_date": exam.start_date,
                "end_date": exam.end_date,
                "status": exam.get_status_display(),
                "subjects_count": subjects.count(),
                "subjects": ", ".join([s.subject.name for s in subjects]),
            })
        return rows


class ExamMarksReportView(AggregateReportView):
    """Exam marks report for a specific exam."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "exam_marks"
    model = "apps.exams.models.StudentResult"

    def get_base_queryset(self, request):
        from apps.exams.models import StudentResult
        return StudentResult.objects.select_related(
            "exam", "exam__campus", "exam__class_obj", "exam__academic_year",
            "student", "exam_subject", "exam_subject__subject"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        exam = request.query_params.get("exam")
        if not exam:
            return queryset.none()
        queryset = queryset.filter(exam_id=exam)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        subject = request.query_params.get("subject")
        if subject:
            queryset = queryset.filter(exam_subject_id=subject)

        student = request.query_params.get("student")
        if student:
            queryset = queryset.filter(student_id=student)

        return queryset

    def get_summary(self, queryset, request):
        exam_id = request.query_params.get("exam")
        from apps.exams.models import ExamSubject
        subjects = ExamSubject.objects.filter(exam_id=exam_id).select_related("subject")

        total_results = queryset.count()
        passed = queryset.filter(is_pass=True).count()
        absent = queryset.filter(is_absent=True).count()

        return {
            "total_results": total_results,
            "passed": passed,
            "failed": total_results - passed - absent,
            "absent": absent,
            "pass_rate": round(passed / (total_results - absent) * 100, 2) if total_results > absent else 0,
            "subjects_count": subjects.count(),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for result in queryset:
            percentage = result.percentage
            rows.append({
                "admission_number": result.student.admission_number,
                "student": result.student.full_name,
                "subject": result.exam_subject.subject.name,
                "max_marks": result.exam_subject.maximum_marks,
                "passing_marks": result.exam_subject.passing_marks,
                "obtained_marks": float(result.obtained_marks),
                "percentage": float(percentage),
                "grade": result.grade,
                "is_pass": result.is_pass,
                "is_absent": result.is_absent,
                "remarks": result.remarks,
            })
        return rows


class SubjectPerformanceReportView(AggregateReportView):
    """Per-subject performance statistics."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "subject_performance"
    model = "apps.exams.models.StudentResult"

    def get_base_queryset(self, request):
        from apps.exams.models import StudentResult
        return StudentResult.objects.select_related(
            "exam", "exam__campus", "exam__class_obj",
            "exam_subject", "exam_subject__subject"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        exam = request.query_params.get("exam")
        if not exam:
            return queryset.none()
        queryset = queryset.filter(exam_id=exam, is_absent=False)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        return queryset

    def get_summary(self, queryset, request):
        total_results = queryset.count()
        subjects = {}

        for result in queryset:
            subject_name = result.exam_subject.subject.name
            max_marks = result.exam_subject.maximum_marks
            percentage = float(result.obtained_marks) / max_marks * 100 if max_marks else 0

            if subject_name not in subjects:
                subjects[subject_name] = {
                    "students": 0, "passed": 0, "total_pct": 0,
                    "highest": 0, "lowest": 100,
                }
            s = subjects[subject_name]
            s["students"] += 1
            s["passed"] += int(result.is_pass)
            s["total_pct"] += percentage
            s["highest"] = max(s["highest"], percentage)
            s["lowest"] = min(s["lowest"], percentage)

        return {
            "subjects": len(subjects),
            "total_results": total_results,
        }

    def get_detail_rows(self, queryset, request):
        subjects = {}
        for result in queryset:
            subject_name = result.exam_subject.subject.name
            max_marks = result.exam_subject.maximum_marks
            percentage = float(result.obtained_marks) / max_marks * 100 if max_marks else 0

            if subject_name not in subjects:
                subjects[subject_name] = {
                    "subject": subject_name,
                    "students": 0, "passed": 0, "total_pct": 0,
                    "highest": 0, "lowest": 100,
                }
            s = subjects[subject_name]
            s["students"] += 1
            s["passed"] += int(result.is_pass)
            s["total_pct"] += percentage
            s["highest"] = max(s["highest"], percentage)
            s["lowest"] = min(s["lowest"], percentage)

        rows = []
        for s in subjects.values():
            s["average_percentage"] = round(s["total_pct"] / s["students"], 2) if s["students"] else 0
            s["pass_rate"] = round(s["passed"] / s["students"] * 100, 2) if s["students"] else 0
            s["highest"] = round(s["highest"], 2)
            s["lowest"] = round(s["lowest"], 2)
            rows.append(s)

        return sorted(rows, key=lambda x: x["subject"])


class ClassMarksReportView(AggregateReportView):
    """Class-wise marks summary for an exam."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "class_marks"
    model = "apps.exams.models.StudentResult"

    def get_base_queryset(self, request):
        from apps.exams.models import StudentResult
        return StudentResult.objects.select_related(
            "exam", "exam__campus", "exam__class_obj",
            "student", "exam_subject__subject"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        exam = request.query_params.get("exam")
        if not exam:
            return queryset.none()
        queryset = queryset.filter(exam_id=exam)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        return queryset

    def get_summary(self, queryset, request):
        from apps.reportcards.models import ReportCard
        report_cards = ReportCard.objects.filter(exam__id=request.query_params.get("exam"))
        total = report_cards.count()
        passed = report_cards.filter(overall_result="Pass").count()

        return {
            "total_students": total,
            "passed": passed,
            "pass_rate": round(passed / total * 100, 2) if total else 0,
        }

    def get_detail_rows(self, queryset, request):
        from apps.reportcards.models import ReportCard

        exam_id = request.query_params.get("exam")
        report_cards = ReportCard.objects.filter(exam_id=exam_id).select_related(
            "student", "exam__campus", "exam__class_obj"
        )

        classes = {}
        for rc in report_cards:
            campus = rc.exam.campus.name if rc.exam.campus else "-"
            class_name = rc.exam.class_obj.name if rc.exam.class_obj else "-"
            key = (campus, class_name)

            if key not in classes:
                classes[key] = {
                    "campus": campus, "class": class_name,
                    "students": 0, "passed": 0, "total_pct": 0,
                    "highest": Decimal("0"), "lowest": None,
                }
            c = classes[key]
            c["students"] += 1
            if rc.is_pass:
                c["passed"] += 1
            c["total_pct"] += rc.percentage
            if rc.percentage > c["highest"]:
                c["highest"] = rc.percentage
            if c["lowest"] is None or rc.percentage < c["lowest"]:
                c["lowest"] = rc.percentage

        rows = []
        for c in classes.values():
            c["failed"] = c["students"] - c["passed"]
            c["pass_rate"] = round(c["passed"] / c["students"] * 100, 2) if c["students"] else 0
            c["average_percentage"] = round(float(c["total_pct"] / c["students"]), 2) if c["students"] else 0
            c["highest"] = round(float(c["highest"]), 2)
            c["lowest"] = round(float(c["lowest"]), 2) if c["lowest"] is not None else 0
            rows.append(c)

        return sorted(rows, key=lambda x: (x["campus"], x["class"]))


class StudentResultReportView(BaseReportView):
    """Detailed student result for an exam."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "student_result"
    model = "apps.reportcards.models.ReportCard"

    def get_base_queryset(self, request):
        from apps.reportcards.models import ReportCard
        return ReportCard.objects.select_related(
            "student", "exam", "exam__campus", "exam__class_obj", "exam__academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        exam = request.query_params.get("exam")
        student = request.query_params.get("student")

        if exam:
            queryset = queryset.filter(exam_id=exam)
        if student:
            queryset = queryset.filter(student_id=student)

        queryset = apply_campus_scope(queryset, request, "exam__campus_id")
        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)

        # If single student + exam, return detailed report card
        exam = request.query_params.get("exam")
        student = request.query_params.get("student")

        if exam and student:
            try:
                report_card = queryset.get()
                return Response(self.build_detailed_report_card(report_card))
            except queryset.model.DoesNotExist:
                return Response({"detail": "Report card not found"}, status=404)
            except queryset.model.MultipleObjectsReturned:
                pass

        # Otherwise return list
        rows = []
        for rc in queryset:
            rows.append({
                "id": rc.id,
                "admission_number": rc.student.admission_number,
                "student": rc.student.full_name,
                "exam": rc.exam.name,
                "campus": rc.exam.campus.name if rc.exam.campus else "-",
                "class": rc.exam.class_obj.name if rc.exam.class_obj else "-",
                "total_marks": float(rc.total_marks),
                "maximum_marks": float(rc.maximum_marks),
                "percentage": float(rc.percentage),
                "grade": rc.grade,
                "result": rc.overall_result,
                "position": rc.position,
                "status": rc.get_status_display(),
            })

        return Response({"results": rows})

    def build_detailed_report_card(self, rc):
        from apps.exams.models import StudentResult
        results = StudentResult.objects.filter(
            exam=rc.exam, student=rc.student
        ).select_related("exam_subject__subject")

        subjects = []
        for result in results:
            subjects.append({
                "subject": result.exam_subject.subject.name,
                "max_marks": result.exam_subject.maximum_marks,
                "passing_marks": result.exam_subject.passing_marks,
                "obtained_marks": float(result.obtained_marks),
                "percentage": float(result.percentage),
                "grade": result.grade,
                "is_pass": result.is_pass,
                "is_absent": result.is_absent,
                "remarks": result.remarks,
            })

        return {
            "student": {
                "admission_number": rc.student.admission_number,
                "full_name": rc.student.full_name,
                "photo": rc.student.photo.url if rc.student.photo else None,
                "gender": rc.student.gender,
                "date_of_birth": rc.student.date_of_birth,
            },
            "exam": {
                "name": rc.exam.name,
                "type": rc.exam.get_exam_type_display(),
                "campus": rc.exam.campus.name if rc.exam.campus else "-",
                "class": rc.exam.class_obj.name if rc.exam.class_obj else "-",
                "academic_year": rc.exam.academic_year.name,
                "start_date": rc.exam.start_date,
                "end_date": rc.exam.end_date,
            },
            "summary": {
                "total_marks": float(rc.total_marks),
                "maximum_marks": float(rc.maximum_marks),
                "percentage": float(rc.percentage),
                "grade": rc.grade,
                "gpa": float(rc.grade_point),
                "result": rc.overall_result,
                "position": rc.position,
                "teacher_remarks": rc.teacher_remarks,
                "principal_remarks": rc.principal_remarks,
            },
            "subjects": subjects,
            "attendance": self.get_attendance_summary(rc.student, rc.exam),
        }

    def get_attendance_summary(self, student, exam):
        from apps.attendance.models import Attendance
        from apps.students.models import Enrollment

        enrollment = Enrollment.objects.filter(
            student=student,
            academic_year=exam.academic_year,
            campus=exam.campus,
            class_obj=exam.class_obj,
            status="active"
        ).first()

        if not enrollment:
            return None

        attendance = Attendance.objects.filter(
            student=student,
            enrollment=enrollment,
            date__gte=exam.academic_year.start_date,
            date__lte=exam.end_date,
        )

        total = attendance.count()
        present = attendance.filter(status="present").count()
        absent = attendance.filter(status="absent").count()
        late = attendance.filter(status="late").count()
        leave = attendance.filter(status="leave").count()

        return {
            "total_days": total,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave,
            "rate": round((present + late) / total * 100, 2) if total else 0,
        }


class ResultAnalyticsReportView(AggregateReportView):
    """Result analytics and comparisons."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "result_analytics"
    model = "apps.reportcards.models.ReportCard"

    def get_base_queryset(self, request):
        from apps.reportcards.models import ReportCard
        return ReportCard.objects.select_related(
            "exam", "exam__campus", "exam__class_obj", "student"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        exam = request.query_params.get("exam")
        if exam:
            queryset = queryset.filter(exam_id=exam)

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(exam__academic_year_id=academic_year)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        passed = queryset.filter(overall_result="Pass").count()
        percentages = [float(rc.percentage) for rc in queryset]

        # Grade distribution
        grade_dist = queryset.values("grade").annotate(count=Count("id")).order_by("grade")

        # Top performers
        top = queryset.order_by("-percentage")[:10]
        top_performers = [
            {
                "admission_number": rc.student.admission_number,
                "name": rc.student.full_name,
                "percentage": float(rc.percentage),
                "grade": rc.grade,
                "position": rc.position,
            } for rc in top
        ]

        # Bottom performers
        bottom = queryset.order_by("percentage")[:10]
        bottom_performers = [
            {
                "admission_number": rc.student.admission_number,
                "name": rc.student.full_name,
                "percentage": float(rc.percentage),
                "grade": rc.grade,
            } for rc in bottom
        ]

        return {
            "total_students": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total * 100, 2) if total else 0,
            "average_percentage": round(sum(percentages) / len(percentages), 2) if percentages else 0,
            "highest": round(max(percentages), 2) if percentages else 0,
            "lowest": round(min(percentages), 2) if percentages else 0,
            "grade_distribution": list(grade_dist),
            "top_performers": top_performers,
            "bottom_performers": bottom_performers,
        }

    def get_detail_rows(self, queryset, request):
        return []


class StudentRankingReportView(AggregateReportView):
    """Student rankings within class/campus."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "student_ranking"
    model = "apps.reportcards.models.ReportCard"

    def get_base_queryset(self, request):
        from apps.reportcards.models import ReportCard
        return ReportCard.objects.select_related(
            "student", "exam", "exam__campus", "exam__class_obj"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        exam = request.query_params.get("exam")
        if not exam:
            return queryset.none()
        queryset = queryset.filter(exam_id=exam)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        return queryset

    def get_summary(self, queryset, request):
        return {"total_students": queryset.count()}

    def get_detail_rows(self, queryset, request):
        # Rank by percentage
        ranked = sorted(queryset, key=lambda rc: rc.percentage, reverse=True)

        rows = []
        for rank, rc in enumerate(ranked, 1):
            rows.append({
                "rank": rank,
                "admission_number": rc.student.admission_number,
                "student": rc.student.full_name,
                "campus": rc.exam.campus.name if rc.exam.campus else "-",
                "class": rc.exam.class_obj.name if rc.exam.class_obj else "-",
                "percentage": float(rc.percentage),
                "grade": rc.grade,
                "result": rc.overall_result,
                "position": rc.position,
            })
        return rows


class ReportCardGeneratorView(BaseReportView):
    """Professional report card generation."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "report_card"
    model = "apps.reportcards.models.ReportCard"

    def get_base_queryset(self, request):
        from apps.reportcards.models import ReportCard
        return ReportCard.objects.select_related(
            "student", "exam", "exam__campus", "exam__class_obj", "exam__academic_year"
        ).prefetch_related("exam__exam_subjects__subject")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        exam = request.query_params.get("exam")
        if exam:
            queryset = queryset.filter(exam_id=exam)

        student = request.query_params.get("student")
        if student:
            queryset = queryset.filter(student_id=student)

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)

        # Check if bulk generation requested
        bulk = request.query_params.get("bulk") == "true"
        format_type = request.query_params.get("export_format", "json")

        if bulk and format_type == "pdf":
            return self.generate_bulk_pdf(queryset, request)

        report_cards = []
        for rc in queryset:
            report_cards.append(self.build_report_card_data(rc))

        return Response({
            "count": len(report_cards),
            "report_cards": report_cards,
        })

    def build_report_card_data(self, rc):
        from apps.exams.models import StudentResult
        from apps.reports.models import ReportTemplate

        results = StudentResult.objects.filter(
            exam=rc.exam, student=rc.student
        ).select_related("exam_subject__subject").order_by("exam_subject__subject__name")

        # Get template
        template = ReportTemplate.objects.filter(
            report_type="report_card", is_default=True
        ).first()

        subjects = []
        for result in results:
            subjects.append({
                "subject": result.exam_subject.subject.name,
                "max_marks": result.exam_subject.maximum_marks,
                "passing_marks": result.exam_subject.passing_marks,
                "obtained_marks": float(result.obtained_marks),
                "percentage": float(result.percentage),
                "grade": result.grade,
                "is_pass": result.is_pass,
                "is_absent": result.is_absent,
                "remarks": result.remarks,
            })

        # School branding
        school = rc.exam.campus.school if rc.exam.campus else None
        campus = rc.exam.campus

        return {
            "school": {
                "name": school.name if school else "Perfect Foundation School",
                "logo": school.settings.logo.url if school and school.settings.logo else None,
                "address": school.address if school else "",
                "phone": school.settings.contact_phone if school and school.settings else "",
                "email": school.settings.contact_email if school and school.settings else "",
            },
            "campus": {
                "name": campus.name if campus else "Main Campus",
                "address": campus.address if campus else "",
            },
            "student": {
                "admission_number": rc.student.admission_number,
                "full_name": rc.student.full_name,
                "photo": rc.student.photo.url if rc.student.photo else None,
                "gender": rc.student.gender,
                "date_of_birth": rc.student.date_of_birth,
                "class": rc.exam.class_obj.name if rc.exam.class_obj else "-",
                "section": rc.student.enrollments.filter(
                    exam=rc.exam, status="active"
                ).first().section.name if rc.student.enrollments.filter(
                    exam=rc.exam, status="active"
                ).first().section else "-",
            },
            "exam": {
                "name": rc.exam.name,
                "type": rc.exam.get_exam_type_display(),
                "academic_year": rc.exam.academic_year.name,
            },
            "subjects": subjects,
            "summary": {
                "total_marks": float(rc.total_marks),
                "maximum_marks": float(rc.maximum_marks),
                "percentage": float(rc.percentage),
                "grade": rc.grade,
                "gpa": float(rc.grade_point),
                "result": rc.overall_result,
                "position": rc.position,
            },
            "teacher_remarks": rc.teacher_remarks,
            "principal_remarks": rc.principal_remarks,
            "attendance": self.get_attendance_summary(rc.student, rc.exam),
            "template_config": {
                "header": template.header_config if template else {},
                "footer": template.footer_config if template else {},
                "page": template.page_config if template else {},
                "styling": template.styling if template else {},
            } if template else {},
        }

    def get_attendance_summary(self, student, exam):
        from apps.attendance.models import Attendance
        from apps.students.models import Enrollment

        enrollment = Enrollment.objects.filter(
            student=student,
            academic_year=exam.academic_year,
            campus=exam.campus,
            class_obj=exam.class_obj,
            status="active"
        ).first()

        if not enrollment:
            return None

        attendance = Attendance.objects.filter(
            student=student,
            enrollment=enrollment,
            date__gte=exam.academic_year.start_date,
            date__lte=exam.end_date,
        )

        total = attendance.count()
        present = attendance.filter(status="present").count()
        absent = attendance.filter(status="absent").count()
        late = attendance.filter(status="late").count()
        leave = attendance.filter(status="leave").count()

        return {
            "total_days": total,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave,
            "rate": round((present + late) / total * 100, 2) if total else 0,
        }

    def generate_bulk_pdf(self, queryset, request):
        # Placeholder for bulk PDF generation
        return Response({"detail": "Bulk PDF generation not yet implemented"}, status=501)