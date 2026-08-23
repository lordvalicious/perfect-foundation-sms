from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from apps.accounts.scopes import (
    get_student_profile,
    is_manager,
    is_parent,
    is_teacher,
    parent_student_ids,
    teacher_student_ids,
)


def _serialize_student(student):
    enrollment = (
        student.enrollments
        .filter(status="active")
        .select_related("class_obj")
        .first()
    )

    return {
        "type": "student",
        "id": student.pk,
        "name": student.full_name,
        "subtitle": f"{student.admission_number}",
        "class_name": (
            enrollment.class_obj.name
            if enrollment and enrollment.class_obj_id
            else ""
        ),
        "link": f"/students/{student.pk}",
    }


def _serialize_guardian(guardian):
    return {
        "type": "guardian",
        "id": guardian.pk,
        "name": guardian.name,
        "subtitle": guardian.relationship or "Guardian",
        "link": f"/students?guardian={guardian.pk}",
    }


def _serialize_teacher(teacher):
    return {
        "type": "teacher",
        "id": teacher.pk,
        "name": teacher.full_name,
        "subtitle": (
            teacher.designation or "Teacher"
        ),
        "link": f"/teachers/{teacher.pk}",
    }


def _serialize_class(class_obj):
    return {
        "type": "class",
        "id": class_obj.pk,
        "name": class_obj.name,
        "subtitle": (
            class_obj.unit.campus.name
            if class_obj.unit_id
            else ""
        ),
        "link": f"/students?class_obj={class_obj.pk}",
    }


def _serialize_subject(subject):
    return {
        "type": "subject",
        "id": subject.pk,
        "name": subject.name,
        "subtitle": subject.code or "Subject",
        "link": f"/teachers?subject={subject.pk}",
    }


def _serialize_exam(exam):
    return {
        "type": "exam",
        "id": exam.pk,
        "name": exam.name,
        "subtitle": exam.class_obj.name,
        "link": f"/exams/{exam.pk}",
    }


def _serialize_invoice(invoice):
    return {
        "type": "invoice",
        "id": invoice.pk,
        "name": f"Invoice {invoice.invoice_number}",
        "subtitle": invoice.student.full_name,
        "link": f"/finance?invoice={invoice.pk}",
    }


class GlobalSearchView(APIView):
    """Search across the system in a single request."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if len(query) < 2:
            return Response({"results": []})

        user = request.user

        results = []

        if is_manager(user):
            results.extend(self._search_students(query))
            results.extend(self._search_guardians(query))
            results.extend(self._search_teachers(query))
            results.extend(self._search_classes(query))
            results.extend(self._search_subjects(query))
            results.extend(self._search_exams(query))
            results.extend(self._search_invoices(query))
            results.extend(self._search_users(query))
        elif is_teacher(user):
            student_ids = teacher_student_ids(user)
            results.extend(
                self._search_students(query, student_ids=student_ids)
            )
            results.extend(self._search_classes(query, teacher=True))
            results.extend(self._search_subjects(query, teacher=True))
            results.extend(self._search_exams(query, teacher=True))
        elif is_parent(user):
            student_ids = parent_student_ids(user)
            results.extend(
                self._search_students(query, student_ids=student_ids)
            )
        else:
            profile = get_student_profile(user)

            if profile is not None:
                results.extend(
                    self._search_students(
                        query,
                        student_ids=[profile.pk],
                    )
                )

        return Response({"results": results[:50]})

    def _search_students(self, query, student_ids=None):
        from apps.students.models import Student

        queryset = (
            Student.objects
            .filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(middle_name__icontains=query)
                | Q(admission_number__icontains=query),
                enrollments__academic_year__school=self.request.institution,
            )
        )

        if student_ids is not None:
            queryset = queryset.filter(pk__in=student_ids)

        queryset = apply_campus_scope(
            queryset,
            self.request,
            "enrollments__campus_id",
        )

        return [
            _serialize_student(student)
            for student in queryset[:10]
        ]

    def _search_guardians(self, query):
        from apps.students.models import Guardian

        queryset = Guardian.objects.filter(
            Q(name__icontains=query)
            | Q(phone__icontains=query),
            guardian_links__student__enrollments__academic_year__school=self.request.institution,
        )
        queryset = apply_campus_scope(
            queryset,
            self.request,
            "guardian_links__student__enrollments__campus_id",
        ).distinct()

        return [
            _serialize_guardian(guardian)
            for guardian in queryset[:10]
        ]

    def _search_teachers(self, query):
        from apps.teachers.models import Teacher

        queryset = Teacher.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(employee_number__icontains=query)
            | Q(designation__icontains=query),
            membership__institution=self.request.institution,
        )
        queryset = apply_campus_scope(
            queryset,
            self.request,
            "primary_campus_id",
        )

        return [
            _serialize_teacher(teacher)
            for teacher in queryset[:10]
        ]

    def _search_classes(self, query, teacher=False):
        from apps.schools.models import Class as SchoolClass

        if teacher:
            from apps.accounts.scopes import teacher_class_ids

            class_ids = teacher_class_ids(self.request.user)

            queryset = SchoolClass.objects.filter(
                pk__in=class_ids,
                name__icontains=query,
            )
        else:
            queryset = SchoolClass.objects.filter(
                unit__campus__school=self.request.institution,
                name__icontains=query,
            )
            queryset = apply_campus_scope(
                queryset,
                self.request,
                "unit__campus_id",
            )

        return [
            _serialize_class(class_obj)
            for class_obj in queryset[:10]
        ]

    def _search_subjects(self, query, teacher=False):
        from apps.schools.models import Subject

        if teacher:
            from apps.teachers.models import TeacherAssignment

            subject_ids = (
                TeacherAssignment.objects
                .filter(
                    teacher__user=self.request.user,
                    status="active",
                )
                .values_list("subject_id", flat=True)
            )

            queryset = Subject.objects.filter(
                pk__in=subject_ids,
            ).filter(
                Q(name__icontains=query)
                | Q(code__icontains=query),
            )
        else:
            queryset = Subject.objects.filter(
                Q(name__icontains=query)
                | Q(code__icontains=query),
                offerings__class_obj__unit__campus__school=self.request.institution,
            ).distinct()

        return [
            _serialize_subject(subject)
            for subject in queryset[:10]
        ]

    def _search_exams(self, query, teacher=False):
        from apps.exams.models import Exam

        if teacher:
            from apps.accounts.scopes import teacher_class_ids

            class_ids = teacher_class_ids(self.request.user)

            queryset = Exam.objects.filter(
                class_obj_id__in=class_ids,
                name__icontains=query,
            )
        else:
            queryset = Exam.objects.filter(
                class_obj__unit__campus__school=self.request.institution,
                name__icontains=query,
            )
            queryset = apply_campus_scope(
                queryset,
                self.request,
                "class_obj__unit__campus_id",
            )

        return [
            _serialize_exam(exam)
            for exam in queryset.select_related("class_obj")[:10]
        ]

    def _search_invoices(self, query):
        from apps.finance.models import Invoice

        from apps.finance.views import scoped_invoice_queryset

        queryset = scoped_invoice_queryset(self.request).filter(
            Q(invoice_number__icontains=query)
            | Q(student__first_name__icontains=query)
            | Q(student__last_name__icontains=query)
        ).select_related("student")

        return [
            _serialize_invoice(invoice)
            for invoice in queryset[:10]
        ]

    def _search_users(self, query):
        from apps.accounts.models import User

        users = (
            User.objects
            .filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(username__icontains=query)
                | Q(email__icontains=query),
                memberships__institution=self.request.institution,
            )
            .distinct()[:10]
        )

        results = []

        for user in users:
            role = user.primary_role or "user"

            results.append(
                {
                    "type": "user",
                    "id": user.pk,
                    "name": user.get_full_name() or user.username,
                    "subtitle": role,
                    "link": f"/staff?user={user.pk}",
                }
            )

        return results
