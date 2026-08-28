"""Class, Section, Subject, and Timetable Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class ClassStrengthReportView(AggregateReportView):
    """Class strength report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "class_strength"
    model = "apps.students.models.Enrollment"

    def get_base_queryset(self, request):
        from apps.students.models import Enrollment
        return Enrollment.objects.filter(status="active").select_related(
            "student", "campus", "class_obj", "section", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_class = queryset.values("class_obj__name").annotate(count=Count("id")).order_by("class_obj__name")
        by_campus = queryset.values("campus__name").annotate(count=Count("id"))

        return {
            "total_students": total,
            "total_classes": by_class.count(),
            "by_class": list(by_class),
            "by_campus": list(by_campus),
        }

    def get_detail_rows(self, queryset, request):
        classes = {}
        for enrollment in queryset:
            campus = enrollment.campus.name
            class_name = enrollment.class_obj.name
            section = enrollment.section.name if enrollment.section else "-"
            key = (campus, class_name, section)

            if key not in classes:
                classes[key] = {
                    "campus": campus,
                    "class": class_name,
                    "section": section,
                    "count": 0,
                    "male": 0,
                    "female": 0,
                }
            classes[key]["count"] += 1
            if enrollment.student.gender == "male":
                classes[key]["male"] += 1
            else:
                classes[key]["female"] += 1

        rows = []
        for c in classes.values():
            rows.append({
                "campus": c["campus"],
                "class": c["class"],
                "section": c["section"],
                "total": c["count"],
                "male": c["male"],
                "female": c["female"],
            })

        return sorted(rows, key=lambda x: (x["campus"], x["class"], x["section"]))


class SectionStrengthReportView(ClassStrengthReportView):
    """Section strength report."""
    report_definition_key = "section_strength"


class ClassStudentListReportView(AggregateReportView):
    """Student list by class."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "class_student_list"
    model = "apps.students.models.Enrollment"

    def get_base_queryset(self, request):
        from apps.students.models import Enrollment
        return Enrollment.objects.filter(status="active").select_related(
            "student", "campus", "class_obj", "section", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        class_obj = request.query_params.get("class")
        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        section = request.query_params.get("section")
        if section:
            queryset = queryset.filter(section_id=section)

        return queryset

    def get_summary(self, queryset, request):
        return {
            "total_students": queryset.count(),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for enrollment in queryset:
            rows.append({
                "roll_number": enrollment.roll_number,
                "admission_number": enrollment.student.admission_number,
                "full_name": enrollment.student.full_name,
                "gender": enrollment.student.gender,
                "date_of_birth": enrollment.student.date_of_birth,
                "campus": enrollment.campus.name,
                "class": enrollment.class_obj.name,
                "section": enrollment.section.name if enrollment.section else "-",
                "guardian": enrollment.student.guardian.name if enrollment.student.guardian else "-",
                "phone": enrollment.student.phone,
            })
        return rows


class GenderDistributionReportView(AggregateReportView):
    """Gender distribution report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "gender_distribution"
    model = "apps.students.models.Student"

    def get_base_queryset(self, request):
        from apps.students.models import Student
        return Student.objects.filter(status="active").select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        male = queryset.filter(gender="male").count()
        female = queryset.filter(gender="female").count()

        by_campus = queryset.values("primary_campus__name").annotate(
            male=Count(Case(When(gender="male", then=1))),
            female=Count(Case(When(gender="female", then=1))),
            total=Count("id"),
        )

        by_class = queryset.values("enrollments__class_obj__name").annotate(
            male=Count(Case(When(gender="male", then=1))),
            female=Count(Case(When(gender="female", then=1))),
            total=Count("id"),
        ).filter(enrollments__status="active")

        return {
            "total": total,
            "male": male,
            "female": female,
            "male_percent": round(male / total * 100, 2) if total else 0,
            "female_percent": round(female / total * 100, 2) if total else 0,
            "by_campus": list(by_campus),
            "by_class": list(by_class),
        }

    def get_detail_rows(self, queryset, request):
        return []


class AcademicPerformanceReportView(AggregateReportView):
    """Class academic performance report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "class_academic_performance"
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

        classes = {}
        for rc in queryset:
            campus = rc.exam.campus.name if rc.exam.campus else "-"
            class_name = rc.exam.class_obj.name if rc.exam.class_obj else "-"
            key = (campus, class_name)

            if key not in classes:
                classes[key] = {"campus": campus, "class": class_name, "students": 0, "passed": 0, "total_pct": Decimal("0")}
            c = classes[key]
            c["students"] += 1
            if rc.is_pass:
                c["passed"] += 1
            c["total_pct"] += rc.percentage

        return {
            "total_students": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total * 100, 2) if total else 0,
        }

    def get_detail_rows(self, queryset, request):
        classes = {}
        for rc in queryset:
            campus = rc.exam.campus.name if rc.exam.campus else "-"
            class_name = rc.exam.class_obj.name if rc.exam.class_obj else "-"
            key = (campus, class_name)

            if key not in classes:
                classes[key] = {"campus": campus, "class": class_name, "students": 0, "passed": 0, "total_pct": Decimal("0")}
            c = classes[key]
            c["students"] += 1
            if rc.is_pass:
                c["passed"] += 1
            c["total_pct"] += rc.percentage

        rows = []
        for c in classes.values():
            c["failed"] = c["students"] - c["passed"]
            c["pass_rate"] = round(c["passed"] / c["students"] * 100, 2) if c["students"] else 0
            c["average_percentage"] = round(float(c["total_pct"] / c["students"]), 2) if c["students"] else 0
            rows.append(c)

        return sorted(rows, key=lambda x: (x["campus"], x["class"]))


class PromotionReportView(AggregateReportView):
    """Student promotion report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "promotion_report"
    model = "apps.students.models.StudentLifecycleEvent"

    def get_base_queryset(self, request):
        from apps.students.models import StudentLifecycleEvent
        return StudentLifecycleEvent.objects.filter(
            event_type__in=["graduated", "transferred"]
        ).select_related("student", "from_campus", "to_campus", "from_enrollment", "to_enrollment", "recorded_by")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        event_type = request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(effective_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(effective_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_type = queryset.values("event_type").annotate(count=Count("id"))
        by_campus = queryset.values("from_campus__name").annotate(count=Count("id"))

        return {
            "total_events": total,
            "by_type": list(by_type),
            "by_campus": list(by_campus),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for event in queryset:
            rows.append({
                "admission_number": event.student.admission_number,
                "student": event.student.full_name,
                "event_type": event.get_event_type_display(),
                "effective_date": event.effective_date,
                "from_campus": event.from_campus.name if event.from_campus else "-",
                "to_campus": event.to_campus.name if event.to_campus else "-",
                "from_class": event.from_enrollment.class_obj.name if event.from_enrollment else "-",
                "to_class": event.to_enrollment.class_obj.name if event.to_enrollment else "-",
                "reason": event.reason,
                "recorded_by": event.recorded_by.get_full_name() if event.recorded_by else "-",
            })
        return rows


class SubjectListReportView(AggregateReportView):
    """Subject list report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "subject_list"
    model = "apps.schools.models.Subject"

    def get_base_queryset(self, request):
        from apps.schools.models import Subject
        return Subject.objects.filter(status="active").select_related("institution")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        subject_type = request.query_params.get("subject_type")
        if subject_type:
            queryset = queryset.filter(subject_type=subject_type)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_type = queryset.values("subject_type").annotate(count=Count("id"))

        return {
            "total_subjects": total,
            "by_type": list(by_type),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for subject in queryset:
            rows.append({
                "code": subject.code,
                "name": subject.name,
                "type": subject.get_subject_type_display(),
                "practical_required": "Yes" if subject.practical_required else "No",
            })
        return rows


class SubjectAllocationReportView(AggregateReportView):
    """Subject allocation to teachers."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "subject_allocation"
    model = "apps.schools.models.SubjectOffering"

    def get_base_queryset(self, request):
        from apps.schools.models import SubjectOffering
        return SubjectOffering.objects.filter(status="active").select_related(
            "subject", "class_obj", "teacher", "teacher__user", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "class_obj__unit__campus_id")

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        with_teacher = queryset.filter(teacher__isnull=False).count()
        without_teacher = total - with_teacher

        return {
            "total_offerings": total,
            "with_teacher": with_teacher,
            "without_teacher": without_teacher,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for offering in queryset:
            rows.append({
                "subject": offering.subject.name,
                "class": offering.class_obj.name,
                "academic_year": offering.academic_year.name,
                "teacher": offering.teacher.full_name if offering.teacher else "Unassigned",
                "teacher_email": offering.teacher.user.email if offering.teacher and offering.teacher.user else "-",
            })
        return rows


class SubjectPerformanceReportView(AggregateReportView):
    """Subject performance across classes."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "subject_performance_report"
    model = "apps.exams.models.StudentResult"

    def get_base_queryset(self, request):
        from apps.exams.models import StudentResult
        return StudentResult.objects.filter(is_absent=False).select_related(
            "exam", "exam__campus", "exam__class_obj", "exam_subject__subject", "student"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        exam = request.query_params.get("exam")
        if exam:
            queryset = queryset.filter(exam_id=exam)

        subject = request.query_params.get("subject")
        if subject:
            queryset = queryset.filter(exam_subject_id=subject)

        return queryset

    def get_summary(self, queryset, request):
        subjects = {}
        for result in queryset:
            subj = result.exam_subject.subject.name
            if subj not in subjects:
                subjects[subj] = {"students": 0, "passed": 0, "total_pct": Decimal("0"), "highest": Decimal("0"), "lowest": None}
            s = subjects[subj]
            s["students"] += 1
            s["passed"] += int(result.is_pass)
            pct = result.percentage
            s["total_pct"] += pct
            if pct > s["highest"]:
                s["highest"] = pct
            if s["lowest"] is None or pct < s["lowest"]:
                s["lowest"] = pct

        return {
            "total_subjects": len(subjects),
        }

    def get_detail_rows(self, queryset, request):
        subjects = {}
        for result in queryset:
            subj = result.exam_subject.subject.name
            pct = result.percentage
            if subj not in subjects:
                subjects[subj] = {"subject": subj, "students": 0, "passed": 0, "total_pct": Decimal("0"), "highest": Decimal("0"), "lowest": None}
            s = subjects[subj]
            s["students"] += 1
            s["passed"] += int(result.is_pass)
            s["total_pct"] += pct
            if pct > s["highest"]:
                s["highest"] = pct
            if s["lowest"] is None or pct < s["lowest"]:
                s["lowest"] = pct

        rows = []
        for s in subjects.values():
            s["failed"] = s["students"] - s["passed"]
            s["pass_rate"] = round(s["passed"] / s["students"] * 100, 2) if s["students"] else 0
            s["average"] = round(float(s["total_pct"] / s["students"]), 2) if s["students"] else 0
            s["highest"] = float(s["highest"])
            s["lowest"] = float(s["lowest"]) if s["lowest"] is not None else 0
            rows.append(s)

        return sorted(rows, key=lambda x: x["subject"])


class TeacherSubjectAllocationReportView(AggregateReportView):
    """Teacher subject allocation report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "teacher_subject_allocation"
    model = "apps.teachers.models.TeacherAssignment"

    def get_base_queryset(self, request):
        from apps.teachers.models import TeacherAssignment
        return TeacherAssignment.objects.filter(status="active").select_related(
            "teacher", "teacher__user", "campus", "class_obj", "section", "subject", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset

    def get_summary(self, queryset, request):
        teachers = {}
        for a in queryset:
            tid = a.teacher_id
            if tid not in teachers:
                teachers[tid] = {"teacher": a.teacher.full_name, "subjects": set(), "classes": set()}
            teachers[tid]["subjects"].add(a.subject.name)
            teachers[tid]["classes"].add(a.class_obj.name)

        return {
            "total_teachers": len(teachers),
            "total_assignments": queryset.count(),
        }

    def get_detail_rows(self, queryset, request):
        teachers = {}
        for a in queryset:
            tid = a.teacher_id
            if tid not in teachers:
                teachers[tid] = {
                    "teacher": a.teacher.full_name,
                    "employee_number": a.teacher.employee_number,
                    "campus": a.campus.name,
                    "subjects": set(),
                    "classes": set(),
                    "sections": set(),
                }
            t = teachers[tid]
            t["subjects"].add(a.subject.name)
            t["classes"].add(a.class_obj.name)
            t["sections"].add(a.section.name)

        rows = []
        for t in teachers.values():
            t["subjects"] = ", ".join(sorted(t["subjects"]))
            t["classes"] = ", ".join(sorted(t["classes"]))
            t["sections"] = ", ".join(sorted(t["sections"]))
            rows.append(t)

        return sorted(rows, key=lambda x: x["teacher"])


class StudentTimetableReportView(BaseReportView):
    """Student timetable report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "timetable_student"
    model = "apps.timetable.models.TimetableEntry"

    def get_base_queryset(self, request):
        from apps.timetable.models import TimetableEntry
        return TimetableEntry.objects.select_related(
            "period", "subject", "teacher", "room", "class_obj", "section", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        student_id = request.query_params.get("student")
        if not student_id:
            return queryset.none()

        from apps.students.models import Enrollment
        enrollment = Enrollment.objects.filter(student_id=student_id, status="active").first()
        if not enrollment:
            return queryset.none()

        queryset = queryset.filter(
            class_obj=enrollment.class_obj,
            section=enrollment.section,
            academic_year=enrollment.academic_year,
        )
        return apply_campus_scope(queryset, request, "class_obj__unit__campus_id")

    def get(self, request):
        queryset = self.get_queryset(request).order_by("period__day", "period__start_time")

        if not queryset.exists():
            return Response({"detail": "No timetable found for this student"}, status=404)

        # Build timetable grid
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        timetable = {day: [] for day in days}

        for entry in queryset:
            day_name = entry.period.get_day_display()
            if day_name in timetable:
                timetable[day_name].append({
                    "period": entry.period.name,
                    "start_time": entry.period.start_time,
                    "end_time": entry.period.end_time,
                    "subject": entry.subject.name,
                    "teacher": entry.teacher.full_name if entry.teacher else "-",
                    "room": entry.room.name if entry.room else "-",
                })

        return Response({
            "timetable": timetable,
            "student_id": request.query_params.get("student"),
        })


class ClassTimetableReportView(StudentTimetableReportView):
    """Class timetable report."""
    report_definition_key = "timetable_class"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        class_obj = request.query_params.get("class")
        section = request.query_params.get("section")
        academic_year = request.query_params.get("academic_year")

        if not class_obj:
            return queryset.none()

        queryset = queryset.filter(class_obj_id=class_obj)

        if section:
            queryset = queryset.filter(section_id=section)
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return apply_campus_scope(queryset, request, "class_obj__unit__campus_id")


class TeacherTimetableReportView(StudentTimetableReportView):
    """Teacher timetable report."""
    report_definition_key = "timetable_teacher"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        teacher_id = request.query_params.get("teacher")
        if not teacher_id:
            return queryset.none()

        queryset = queryset.filter(teacher_id=teacher_id)
        return apply_campus_scope(queryset, request, "class_obj__unit__campus_id")


class RoomTimetableReportView(StudentTimetableReportView):
    """Room timetable report."""
    report_definition_key = "timetable_room"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        room_id = request.query_params.get("room")
        if not room_id:
            return queryset.none()

        queryset = queryset.filter(room_id=room_id)
        return apply_campus_scope(queryset, request, "room__campus_id")


class FreePeriodReportView(AggregateReportView):
    """Free period report for teachers."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "timetable_free_periods"
    model = "apps.teachers.models.Teacher"

    def get_base_queryset(self, request):
        from apps.teachers.models import Teacher
        return Teacher.objects.filter(status="active").select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")
        return queryset

    def get_summary(self, queryset, request):
        return {"total_teachers": queryset.count()}

    def get_detail_rows(self, queryset, request):
        # This would need timetable integration to find free periods
        rows = []
        for teacher in queryset:
            rows.append({
                "teacher": teacher.full_name,
                "employee_number": teacher.employee_number,
                "campus": teacher.primary_campus.name if teacher.primary_campus else "-",
                "note": "Free period calculation requires timetable integration",
            })
        return rows