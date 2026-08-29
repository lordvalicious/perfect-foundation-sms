from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope, assert_campus_allowed
from apps.accounts.permissions import IsAcademicMemberRole, IsTeacherRole
from apps.accounts.scopes import (
    get_student_profile,
    get_teacher_profile,
    is_manager,
    is_parent,
    is_student,
    is_teacher,
    parent_student_class_ids,
    parent_student_ids,
    student_class_ids,
    teacher_class_ids,
    teacher_student_ids,
)
from apps.audit.models import record_audit

from .models import Exam, ExamSchedule, ExamSubject, PracticalResult, StudentResult
from .serializers import (
    ExamScheduleSerializer,
    ExamSerializer,
    ExamSubjectSerializer,
    PracticalResultSerializer,
    StudentResultSerializer,
    StudentResultWriteSerializer,
)


def teacher_can_manage_exam_subject(user, exam_subject):
    """A teacher may manage results for an exam subject only if they
    are actively assigned to teach that subject in the exam's class."""
    if is_manager(user):
        return True

    teacher = get_teacher_profile(user)

    if teacher is None:
        return False

    from apps.teachers.models import TeacherAssignment

    return TeacherAssignment.objects.filter(
        teacher=teacher,
        class_obj=exam_subject.exam.class_obj,
        subject=exam_subject.subject,
        academic_year=exam_subject.exam.academic_year,
        status="active",
    ).exists()


class ExamListPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 500


class ExamListView(generics.ListAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsAcademicMemberRole]
    pagination_class = ExamListPagination

    def get_queryset(self):
        queryset = (
            Exam.objects
            .select_related("academic_year", "campus", "class_obj")
            .prefetch_related("exam_subjects", "results")
            .order_by("-start_date")
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                class_ids = student_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(class_obj_id__in=class_ids)
            elif is_parent(user):
                class_ids = parent_student_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(class_obj_id__in=class_ids)
            elif is_teacher(user):
                class_ids = teacher_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(class_obj_id__in=class_ids)

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
            )

        queryset = apply_campus_scope(queryset, self.request, "campus_id")

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset


class ExamSubjectListView(generics.ListAPIView):
    serializer_class = ExamSubjectSerializer
    permission_classes = [IsAcademicMemberRole]
    pagination_class = None

    def get_queryset(self):
        queryset = (
            ExamSubject.objects
            .select_related("exam", "subject")
            .order_by("exam", "subject__name")
        )

        exam = self.request.query_params.get("exam")

        if exam:
            queryset = queryset.filter(exam_id=exam)

        return queryset


class StudentResultListView(generics.ListCreateAPIView):
    serializer_class = StudentResultSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return StudentResultWriteSerializer

        return StudentResultSerializer

    def get_queryset(self):
        queryset = (
            StudentResult.objects
            .select_related(
                "exam",
                "student",
                "exam_subject__subject",
            )
            .order_by("exam", "student__first_name", "exam_subject__subject__name")
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)
            elif is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(student__first_name__icontains=search)
                | Q(student__middle_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__admission_number__icontains=search)
            )

        exam = self.request.query_params.get("exam")

        if exam:
            queryset = queryset.filter(exam_id=exam)

        grade = self.request.query_params.get("grade")

        if grade:
            queryset = queryset.filter(grade=grade)

        return queryset

    def perform_create(self, serializer):
        exam_subject = serializer.validated_data["exam_subject"]

        if not teacher_can_manage_exam_subject(
            self.request.user,
            exam_subject,
        ):
            raise PermissionDenied(
                "You can only enter marks for subjects you are "
                "assigned to teach."
            )

        result = serializer.save()

        record_audit(
            request=self.request,
            action="create",
            model_name="StudentResult",
            object_id=str(result.pk),
            object_repr=str(result),
            details={
                "exam": result.exam.name,
                "subject": result.exam_subject.subject.name,
                "student": result.student.full_name,
                "marks": str(result.obtained_marks),
            },
        )


class StudentResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StudentResultSerializer
    permission_classes = [IsTeacherRole]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return StudentResultWriteSerializer

        return StudentResultSerializer

    def get_queryset(self):
        queryset = StudentResult.objects.select_related(
            "exam",
            "student",
            "exam_subject__subject",
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)
            elif is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)

        return queryset

    def check_object_write(self, result):
        if not teacher_can_manage_exam_subject(
            self.request.user,
            result.exam_subject,
        ):
            raise PermissionDenied(
                "You can only edit marks for subjects you are "
                "assigned to teach."
            )

    def perform_update(self, serializer):
        instance = self.get_object()
        self.check_object_write(instance)
        serializer.save()

        record_audit(
            request=self.request,
            action="update",
            model_name="StudentResult",
            object_id=str(instance.pk),
            object_repr=str(instance),
            details={"marks": str(instance.obtained_marks)},
        )

    def perform_destroy(self, instance):
        self.check_object_write(instance)
        instance.delete()

        record_audit(
            request=self.request,
            action="delete",
            model_name="StudentResult",
            object_id=str(instance.pk),
            object_repr=str(instance),
        )


class PracticalResultListCreateView(generics.ListCreateAPIView):
    serializer_class = PracticalResultSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_queryset(self):
        queryset = PracticalResult.objects.select_related(
            "exam",
            "student",
            "exam_subject__subject",
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)
            elif is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)

        exam = self.request.query_params.get("exam")

        if exam:
            queryset = queryset.filter(exam_id=exam)

        student = self.request.query_params.get("student")

        if student:
            queryset = queryset.filter(student_id=student)

        exam_subject = self.request.query_params.get("exam_subject")

        if exam_subject:
            queryset = queryset.filter(exam_subject_id=exam_subject)

        return queryset

    def perform_create(self, serializer):
        exam_subject = serializer.validated_data["exam_subject"]

        if not teacher_can_manage_exam_subject(
            self.request.user,
            exam_subject,
        ):
            raise PermissionDenied(
                "You can only enter practical marks for subjects "
                "you are assigned to teach."
            )

        serializer.save()


class PracticalResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PracticalResultSerializer
    permission_classes = [IsTeacherRole]

    def get_queryset(self):
        queryset = PracticalResult.objects.select_related(
            "exam",
            "student",
            "exam_subject__subject",
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)
            elif is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)

        return queryset

    def perform_update(self, serializer):
        instance = self.get_object()

        if not teacher_can_manage_exam_subject(
            self.request.user,
            instance.exam_subject,
        ):
            raise PermissionDenied(
                "You can only edit practical marks for subjects "
                "you are assigned to teach."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if not teacher_can_manage_exam_subject(
            self.request.user,
            instance.exam_subject,
        ):
            raise PermissionDenied(
                "You can only delete practical marks for subjects "
                "you are assigned to teach."
            )

        instance.delete()


class ExamScheduleListView(generics.ListCreateAPIView):
    serializer_class = ExamScheduleSerializer
    permission_classes = [IsAcademicMemberRole]
    pagination_class = ExamListPagination

    def get_queryset(self):
        queryset = (
            ExamSchedule.objects
            .select_related(
                "exam",
                "exam__academic_year",
                "exam__campus",
                "section",
                "section__class_obj",
                "exam_subject__subject",
            )
            .order_by("date", "start_time", "section__name")
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                class_ids = student_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    section__class_obj_id__in=class_ids
                )
            elif is_parent(user):
                class_ids = parent_student_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    section__class_obj_id__in=class_ids
                )
            elif is_teacher(user):
                class_ids = teacher_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    section__class_obj_id__in=class_ids
                )

        exam = self.request.query_params.get("exam")

        if exam:
            queryset = queryset.filter(exam_id=exam)

        section = self.request.query_params.get("section")

        if section:
            queryset = queryset.filter(section_id=section)

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(section__class_obj_id=class_obj)

        date_param = self.request.query_params.get("date")

        if date_param:
            queryset = queryset.filter(date=date_param)

        queryset = apply_campus_scope(
            queryset,
            self.request,
            campus_field="exam__campus_id",
            institution_field="exam__academic_year__school_id",
        )

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if not is_manager(user):
            raise PermissionDenied(
                "Only academic managers can create exam schedules."
            )

        exam = serializer.validated_data["exam"]
        assert_campus_allowed(user, exam.campus_id)

        schedule = serializer.save()

        record_audit(
            request=self.request,
            action="create",
            model_name="ExamSchedule",
            object_id=str(schedule.pk),
            object_repr=str(schedule),
            details={
                "exam": schedule.exam.name,
                "section": schedule.section.name,
                "date": str(schedule.date),
            },
        )


class ExamScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExamScheduleSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_queryset(self):
        queryset = (
            ExamSchedule.objects
            .select_related(
                "exam",
                "exam__academic_year",
                "exam__campus",
                "section",
                "section__class_obj",
                "exam_subject__subject",
            )
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                class_ids = student_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    section__class_obj_id__in=class_ids
                )
            elif is_parent(user):
                class_ids = parent_student_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    section__class_obj_id__in=class_ids
                )
            elif is_teacher(user):
                class_ids = teacher_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    section__class_obj_id__in=class_ids
                )

        queryset = apply_campus_scope(
            queryset,
            self.request,
            campus_field="exam__campus_id",
            institution_field="exam__academic_year__school_id",
        )

        return queryset

    def perform_update(self, serializer):
        user = self.request.user

        if not is_manager(user):
            raise PermissionDenied(
                "Only academic managers can update exam schedules."
            )

        schedule = self.get_object()
        assert_campus_allowed(user, schedule.exam.campus_id)
        serializer.save()

        record_audit(
            request=self.request,
            action="update",
            model_name="ExamSchedule",
            object_id=str(schedule.pk),
            object_repr=str(schedule),
        )

    def perform_destroy(self, instance):
        user = self.request.user

        if not is_manager(user):
            raise PermissionDenied(
                "Only academic managers can delete exam schedules."
            )

        assert_campus_allowed(user, instance.exam.campus_id)
        instance.delete()

        record_audit(
            request=self.request,
            action="delete",
            model_name="ExamSchedule",
            object_id=str(instance.pk),
            object_repr=str(instance),
        )
