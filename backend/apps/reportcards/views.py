from decimal import Decimal

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsAcademicMemberRole,
    IsTeacherRole,
)
from apps.accounts.scopes import (
    get_student_profile,
    is_manager,
    is_parent,
    is_student,
    is_teacher,
    parent_student_ids,
    teacher_student_ids,
)
from apps.audit.models import record_audit

from .models import GradeAmendment, GradeScale, ReportCard
from .serializers import (
    GradeAmendmentCreateSerializer,
    GradeAmendmentSerializer,
    GradeScaleSerializer,
    ReportCardSerializer,
)

REVIEW_ROLES = [
    "super_admin",
    "admin",
    "principal",
    "vice_principal",
    "campus_admin",
    "academic",
]


class ReportCardListView(generics.ListAPIView):
    serializer_class = ReportCardSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_queryset(self):
        queryset = (
            ReportCard.objects
            .select_related("student", "exam", "exam__campus", "exam__class_obj")
            .order_by("exam", "position", "student__first_name")
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

                queryset = queryset.filter(
                    student_id__in=student_ids,
                    status="published",
                )
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

        result = self.request.query_params.get("result")

        if result:
            queryset = queryset.filter(is_pass=(result.lower() == "pass"))

        report_status = self.request.query_params.get("status")

        if report_status:
            queryset = queryset.filter(status=report_status)

        return queryset


class ReportCardDetailView(generics.RetrieveAPIView):
    serializer_class = ReportCardSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_queryset(self):
        queryset = ReportCard.objects.select_related(
            "student",
            "exam",
            "exam__campus",
            "exam__class_obj",
        )

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    student_id__in=student_ids,
                    status="published",
                )
            elif is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)

        return queryset


class ReportCardStatusView(APIView):
    """
    Advance a report card through its workflow:

    draft -> approved -> published

    Approval and publication are restricted to academic
    administrators; teachers cannot publish grades.
    """

    permission_classes = [IsTeacherRole]

    def post(self, request, pk):
        report_card = (
            ReportCard.objects
            .filter(pk=pk)
            .select_related("student", "exam")
            .first()
        )

        if report_card is None:
            return Response(
                {"detail": "Report card not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")

        if new_status not in {"approved", "published"}:
            return Response(
                {
                    "detail": (
                        "Status must be one of: approved, published."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.has_any_role(REVIEW_ROLES):
            raise PermissionDenied(
                "Only academic administrators can change "
                "report card status."
            )

        if new_status == "published":
            report_card.publish(user=request.user)
        elif new_status == "approved":
            if report_card.status == "published":
                raise ValidationError(
                    "A published report card cannot be moved "
                    "back to approved."
                )

            report_card.approve(user=request.user)

        return Response(
            ReportCardSerializer(report_card).data
        )


class GradeScaleListView(generics.ListAPIView):
    serializer_class = GradeScaleSerializer
    permission_classes = [IsTeacherRole]
    pagination_class = None

    def get_queryset(self):
        return (
            GradeScale.objects
            .prefetch_related("bands")
            .order_by("-is_default", "name")
        )


class GradeAmendmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsTeacherRole]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GradeAmendmentCreateSerializer

        return GradeAmendmentSerializer

    def get_queryset(self):
        return (
            GradeAmendment.objects
            .select_related(
                "report_card__student",
                "report_card__exam",
                "exam_subject__subject",
                "amended_by",
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        from django.utils import timezone

        attrs = serializer.validated_data
        result = attrs["_result"]
        report_card = attrs["report_card"]

        maximum = Decimal(str(result.exam_subject.maximum_marks))
        new_marks = attrs["new_obtained_marks"]

        percentage = (new_marks / maximum) * Decimal("100")

        from .models import GradeBand

        band = GradeBand.band_for_percentage(percentage)

        new_grade = band.letter_grade if band else ""
        new_pass = new_marks >= result.exam_subject.passing_marks

        amendment = GradeAmendment.objects.create(
            report_card=report_card,
            exam_subject=result.exam_subject,
            student_result=result,
            previous_obtained_marks=result.obtained_marks,
            new_obtained_marks=new_marks,
            previous_grade=result.grade,
            new_grade=new_grade,
            reason=attrs["reason"],
            amended_by=self.request.user,
        )

        from apps.exams.models import StudentResult

        StudentResult.objects.filter(pk=result.pk).update(
            obtained_marks=new_marks,
            grade=new_grade,
            is_pass=new_pass,
            updated_at=timezone.now(),
        )

        record_audit(
            request=self.request,
            action="grade_amendment",
            model_name="ReportCard",
            object_id=str(report_card.pk),
            object_repr=str(report_card),
            details={
                "amendment_id": amendment.pk,
                "subject": result.exam_subject.subject.name,
                "previous_marks": str(result.obtained_marks),
                "new_marks": str(new_marks),
                "reason": attrs["reason"],
            },
        )
