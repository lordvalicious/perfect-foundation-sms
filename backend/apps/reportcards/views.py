from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, assert_campus_allowed
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

from .pdf import build_report_card_pdf

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
            .prefetch_related("exam__exam_subjects")
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

    def list(self, request, *args, **kwargs):
        """
        Serialize a page of report cards with bulk-loaded results.

        ``ReportCard.results`` and ``is_complete`` each query per
        instance; bulk-populating them here keeps the list view at a
        handful of queries instead of dozens per page.
        """
        from apps.exams.models import StudentResult

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        cards = page if page is not None else list(queryset)

        if cards:
            exam_ids = {card.exam_id for card in cards}
            pairs = {
                (card.exam_id, card.student_id) for card in cards
            }

            grouped = {}
            for result in (
                StudentResult.objects
                .filter(exam_id__in=exam_ids)
                .select_related("exam_subject__subject")
            ):
                if (result.exam_id, result.student_id) in pairs:
                    grouped.setdefault(
                        (result.exam_id, result.student_id), []
                    ).append(result)

            for card in cards:
                card._cached_results = grouped.get(
                    (card.exam_id, card.student_id), []
                )

        serializer = self.get_serializer(cards, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data)


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
    Advance a report card through its lifecycle:

        draft -> submitted -> approved -> published -> locked

    ``unlock`` returns a locked report card to draft through the
    explicit, authorized revision workflow.

    Approval and publication are restricted to academic
    administrators; teachers cannot advance grades alone.
    Campus and organization isolation is enforced so users can only
    transition report cards within their own scope.
    """

    permission_classes = [IsTeacherRole]

    def post(self, request, pk):
        queryset = (
            ReportCard.objects
            .filter(pk=pk)
            .select_related("student", "exam")
        )

        queryset = apply_campus_scope(
            queryset,
            request,
            campus_field="exam__campus_id",
            institution_field="exam__academic_year__school_id",
        )

        report_card = queryset.first()

        if report_card is None:
            return Response(
                {"detail": "Report card not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        action = request.data.get("status")

        if action not in {
            "submitted",
            "approved",
            "published",
            "locked",
            "unlock",
        }:
            return Response(
                {
                    "detail": (
                        "Status must be one of: submitted, approved, "
                        "published, locked, unlock."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.has_any_role(REVIEW_ROLES):
            raise PermissionDenied(
                "Only academic administrators can change "
                "report card status."
            )

        try:
            if action == "submitted":
                report_card.submit(user=request.user)
            elif action == "approved":
                report_card.approve(user=request.user)
            elif action == "published":
                report_card.publish(user=request.user)
            elif action == "locked":
                report_card.lock(user=request.user)
            elif action == "unlock":
                report_card.unlock(user=request.user)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)

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
        queryset = (
            GradeAmendment.objects
            .select_related(
                "report_card__student",
                "report_card__exam",
                "exam_subject__subject",
                "amended_by",
            )
            .order_by("-created_at")
        )

        return apply_campus_scope(
            queryset,
            self.request,
            campus_field="report_card__exam__campus_id",
            institution_field="report_card__exam__academic_year__school_id",
        )

    def perform_create(self, serializer):
        from django.utils import timezone

        attrs = serializer.validated_data
        result = attrs["_result"]
        report_card = attrs["report_card"]

        # IDOR / campus isolation: only amend report cards within scope.
        assert_campus_allowed(
            self.request.user,
            report_card.exam.campus_id,
        )

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


class ReportCardPdfView(APIView):
    """Stream a single report card as a PDF document."""

    permission_classes = [IsAcademicMemberRole]

    def _get_report_card(self, pk):
        report_card = (
            ReportCard.objects
            .select_related(
                "student",
                "exam",
                "exam__campus",
                "exam__class_obj",
            )
            .filter(pk=pk)
            .first()
        )

        if report_card is None:
            return None

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                student_ids = parent_student_ids(user)

                if report_card.student_id not in student_ids:
                    return None

                if report_card.status != "published":
                    return None
            elif is_student(user):
                profile = get_student_profile(user)

                if profile is None or profile.pk != report_card.student_id:
                    return None
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if report_card.student_id not in student_ids:
                    return None

        return report_card

    def get(self, request, pk):
        report_card = self._get_report_card(pk)

        if report_card is None:
            return Response(
                {"detail": "Report card not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        pdf_bytes = build_report_card_pdf(report_card)

        filename = (
            f"report_card_{report_card.student.admission_number}_"
            f"{report_card.exam.pk}.pdf"
        )

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        return response


class ReportCardPdfBatchView(APIView):
    """
    Generate PDF report cards for every student in an exam
    and bundle them into a single ZIP archive.
    """

    permission_classes = [IsAcademicMemberRole]

    def get(self, request):
        from io import BytesIO
        from zipfile import ZIP_DEFLATED, ZipFile

        exam_id = request.query_params.get("exam")

        if not exam_id:
            return Response(
                {"detail": "The exam query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = (
            ReportCard.objects
            .select_related("student", "exam", "exam__class_obj")
            .filter(exam_id=exam_id)
        )

        if queryset.exists() is False:
            return Response(
                {"detail": "No report cards found for this exam."},
                status=status.HTTP_404_NOT_FOUND,
            )

        zip_buffer = BytesIO()

        with ZipFile(zip_buffer, "w", ZIP_DEFLATED) as archive:
            for report_card in queryset:
                pdf_bytes = build_report_card_pdf(report_card)

                filename = (
                    f"{report_card.student.admission_number}_"
                    f"{report_card.student.full_name.replace(' ', '_')}.pdf"
                )

                archive.writestr(filename, pdf_bytes)

        zip_buffer.seek(0)

        exam = queryset.first().exam

        response = HttpResponse(
            zip_buffer.getvalue(),
            content_type="application/zip",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="report_cards_{exam.name}.zip"'
        )

        return response
