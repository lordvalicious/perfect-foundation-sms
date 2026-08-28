from datetime import date
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal

from apps.accounts.access import assert_campus_allowed, campus_access
from apps.accounts.permissions import (
    IsAdminOrReadOnly,
    IsAdminRole,
    IsAcademicMemberRole,
    IsStaffRole,
)
from apps.accounts.scopes import (
    get_guardian_profile,
    get_student_profile,
    is_manager,
    is_parent,
    is_student,
    parent_student_ids,
    parent_scope_filter,
    teacher_scope_filter,
)
from apps.schools.models import AcademicYear

from .models import (
    Guardian,
    Student,
    StudentGuardian,
    AdmissionApplication,
    StudentLifecycleEvent,
    StudentLeaveRequest,
    Enrollment,
    StudentDocument,
    Inquiry,
    AcademicHistory,
    TransferCertificate,
    CampusTransfer,
    SectionTransfer,
    StudentAlumni,
)
from .serializers import (
    EnrollmentCreateSerializer,
    GuardianCreateSerializer,
    GuardianSerializer,
    StudentDocumentSerializer,
    StudentSerializer,
    StudentGuardianSerializer,
    AdmissionApplicationSerializer,
    StudentLifecycleEventSerializer,
    PromotionSerializer,
    StudentLeaveRequestSerializer,
    InquirySerializer,
    InquiryCreateSerializer,
    AcademicHistorySerializer,
    TransferCertificateSerializer,
    TransferCertificateIssueSerializer,
    Student360Serializer,
    CampusTransferSerializer,
    CampusTransferCreateSerializer,
    SectionTransferSerializer,
    SectionTransferCreateSerializer,
    StudentAlumniSerializer,
)


def institution_queryset(queryset, request):
    institution = getattr(request, "institution", None)
    if institution is None:
        return queryset.none()
    return queryset.filter(academic_year__school=institution)


def campus_scoped(queryset, request, field="campus_id"):
    access = campus_access(request)
    if access["global"]:
        if access["requested"]:
            return queryset.filter(**{field: access["requested"]})
        return queryset
    return queryset.filter(**{f"{field}__in": access["allowed_ids"] or [-1]})


class AdmissionApplicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdmissionApplicationSerializer

    def get_queryset(self):
        queryset = institution_queryset(
            AdmissionApplication.objects.select_related(
                "guardian", "campus", "academic_year", "class_obj", "section"
            ),
            self.request,
        )
        queryset = campus_scoped(queryset, self.request)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        campus = self.request.query_params.get("campus")
        if campus:
            assert_campus_allowed(self.request.user, campus)
            queryset = queryset.filter(campus_id=campus)
        return queryset


class AdmissionApplicationDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdmissionApplicationSerializer

    def get_queryset(self):
        return campus_scoped(
            institution_queryset(AdmissionApplication.objects.all(), self.request),
            self.request,
        )


class AdmissionApplicationReviewView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        application = get_object_or_404(
            campus_scoped(
                institution_queryset(AdmissionApplication.objects.select_related("guardian"), request),
                request,
            ),
            pk=pk,
        )
        action = request.data.get("action")
        if action not in ("submit", "under_review", "reject"):
            return Response({"detail": "Invalid review action."}, status=400)
        if action == "submit":
            application.status = "submitted"
            from django.utils import timezone
            application.submitted_at = timezone.now()
        elif action == "under_review":
            application.status = "under_review"
        else:
            application.status = "rejected"
            application.review_notes = request.data.get("review_notes", "")
        application.reviewed_by = request.user
        from django.utils import timezone
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "submitted_at", "reviewed_by", "reviewed_at", "review_notes", "updated_at"])
        return Response(AdmissionApplicationSerializer(application, context={"request": request}).data)


class AdmissionApplicationAcceptView(APIView):
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def post(self, request, pk):
        application = get_object_or_404(
            campus_scoped(
                institution_queryset(AdmissionApplication.objects.select_related("guardian"), request),
                request,
            ),
            pk=pk,
        )
        if application.status not in ("submitted", "under_review"):
            return Response({"detail": "Only submitted applications can be accepted."}, status=400)
        if application.guardian_id is None:
            return Response({"detail": "A guardian is required before acceptance."}, status=400)
        if application.section_id is None:
            return Response({"detail": "A section is required before acceptance."}, status=400)
        admission_number = request.data.get("admission_number") or application.application_number
        if Student.objects.filter(admission_number=admission_number).exists():
            return Response({"detail": "This admission number is already in use."}, status=400)
        student = Student.objects.create(
            admission_number=admission_number,
            primary_campus=application.campus,
            first_name=application.first_name,
            middle_name=application.middle_name,
            last_name=application.last_name,
            date_of_birth=application.date_of_birth,
            gender=application.gender,
            guardian=application.guardian,
            phone=application.phone,
            address=application.address,
            status="active",
            admission_date=date.today(),
        )
        StudentGuardian.objects.create(
            student=student,
            guardian=application.guardian,
            relationship=application.guardian.relationship,
            is_primary=True,
            is_emergency_contact=True,
        )
        enrollment = Enrollment.objects.create(
            student=student,
            academic_year=application.academic_year,
            campus=application.campus,
            class_obj=application.class_obj,
            section=application.section,
            status="active",
        )
        from django.utils import timezone
        application.status = "accepted"
        application.student = student
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "student", "reviewed_by", "reviewed_at", "updated_at"])
        return Response({"student": StudentSerializer(student, context={"request": request}).data, "enrollment_id": enrollment.id}, status=201)


class StudentGuardianListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = StudentGuardianSerializer

    def get_queryset(self):
        queryset = StudentGuardian.objects.select_related("student", "guardian")
        queryset = queryset.filter(
            student__enrollments__academic_year__school=self.request.institution
        )
        queryset = queryset.filter(
            student__enrollments__campus_id__in=campus_access(self.request)["allowed_ids"]
            or [-1]
        ) if not campus_access(self.request)["global"] else queryset
        student = self.request.query_params.get("student")
        if student:
            queryset = queryset.filter(student_id=student)
        return queryset

    def perform_create(self, serializer):
        student = serializer.validated_data["student"]
        if not Student.objects.filter(
            pk=student.pk,
            enrollments__academic_year__school=self.request.institution,
        ).exists():
            raise PermissionDenied("Student is outside the active institution.")
        assert_campus_allowed(
            self.request.user,
            student.enrollments.filter(status="active").values_list("campus_id", flat=True).first(),
        )
        serializer.save()


class StudentLifecycleListView(generics.ListAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = StudentLifecycleEventSerializer

    def get_queryset(self):
        return StudentLifecycleEvent.objects.select_related(
            "student", "from_campus", "to_campus"
        ).filter(student__enrollments__academic_year__school=self.request.institution)


class StudentLifecycleActionView(APIView):
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def post(self, request, pk):
        student = get_object_or_404(
            Student.objects.prefetch_related("enrollments").filter(
                enrollments__academic_year__school=request.institution,
            ),
            pk=pk,
        )
        active = student.enrollments.filter(status="active").select_related("campus").first()
        event_type = request.data.get("event_type")
        if event_type not in dict(StudentLifecycleEvent.EVENT_CHOICES):
            return Response({"detail": "Invalid lifecycle event."}, status=400)
        effective_date = request.data.get("effective_date")
        try:
            effective_date = date.fromisoformat(effective_date) if effective_date else date.today()
        except ValueError:
            return Response({"detail": "effective_date must be YYYY-MM-DD."}, status=400)
        if active:
            assert_campus_allowed(request.user, active.campus_id)
        if event_type in ("withdrawn", "graduated", "inactive"):
            if active:
                active.status = "withdrawn" if event_type == "withdrawn" else "completed"
                active.save(update_fields=["status", "updated_at"])
            student.status = event_type
            student.save(update_fields=["status", "updated_at"])
            event = StudentLifecycleEvent.objects.create(
                student=student,
                event_type=event_type,
                effective_date=effective_date,
                reason=request.data.get("reason", ""),
                from_campus=active.campus if active else None,
                from_enrollment=active,
                recorded_by=request.user,
            )
            return Response(StudentLifecycleEventSerializer(event).data, status=201)
        if event_type == "activated":
            student.status = "active"
            student.save(update_fields=["status", "updated_at"])
            event = StudentLifecycleEvent.objects.create(
                student=student, event_type=event_type, effective_date=effective_date,
                reason=request.data.get("reason", ""), recorded_by=request.user,
            )
            return Response(StudentLifecycleEventSerializer(event).data, status=201)
        required = ["to_academic_year", "to_campus", "to_class_obj", "to_section"]
        missing = [field for field in required if not request.data.get(field)]
        if missing or active is None:
            return Response({"detail": "Transfer requires an active enrollment and destination fields.", "missing": missing}, status=400)
        assert_campus_allowed(request.user, request.data["to_campus"])
        target = Enrollment(
            student=student,
            academic_year_id=request.data["to_academic_year"],
            campus_id=request.data["to_campus"],
            class_obj_id=request.data["to_class_obj"],
            section_id=request.data["to_section"],
            status="active",
        )
        active.status = "completed"
        active.save(update_fields=["status", "updated_at"])
        target.save()
        student.primary_campus_id = target.campus_id
        student.save(update_fields=["primary_campus", "updated_at"])
        event = StudentLifecycleEvent.objects.create(
            student=student, event_type="transferred", effective_date=effective_date,
            reason=request.data.get("reason", ""), from_campus=active.campus,
            to_campus=target.campus, from_enrollment=active, to_enrollment=target,
            recorded_by=request.user,
        )
        return Response(StudentLifecycleEventSerializer(event).data, status=201)


class StudentLeaveRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAcademicMemberRole]
    serializer_class = StudentLeaveRequestSerializer

    def get_queryset(self):
        queryset = StudentLeaveRequest.objects.select_related(
            "student", "requested_by", "reviewed_by"
        ).filter(student__enrollments__academic_year__school=self.request.institution)
        user = self.request.user
        if is_parent(user):
            queryset = queryset.filter(student_id__in=parent_student_ids(user))
        elif is_student(user):
            queryset = queryset.filter(student=get_student_profile(user))
        elif not is_manager(user):
            return queryset.none()
        return queryset.distinct()

    def perform_create(self, serializer):
        user = self.request.user
        student = serializer.validated_data["student"]
        allowed = is_manager(user) or (
            is_parent(user) and student.pk in parent_student_ids(user)
        ) or (
            is_student(user) and get_student_profile(user) == student
        )
        if not allowed:
            raise PermissionDenied("You can only request leave for your own student record.")
        serializer.save(requested_by=user)


class StudentLeaveRequestActionView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        leave = get_object_or_404(
            StudentLeaveRequest.objects.filter(
                student__enrollments__academic_year__school=request.institution,
            ),
            pk=pk,
        )
        action = request.data.get("action")
        if action not in ("approve", "reject", "cancel"):
            return Response({"detail": "Invalid leave action."}, status=400)
        from django.utils import timezone
        leave.status = {"approve": "approved", "reject": "rejected", "cancel": "cancelled"}[action]
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.review_notes = request.data.get("review_notes", "")
        leave.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_notes", "updated_at"])
        return Response(StudentLeaveRequestSerializer(leave).data)


class PromotionView(APIView):
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def post(self, request):
        serializer = PromotionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        years = list(
            AcademicYear.objects.filter(
                pk__in=[data["from_academic_year"], data["to_academic_year"]],
                school=request.institution,
            )
        )
        if len(years) != 2 or data["from_academic_year"] == data["to_academic_year"]:
            return Response({"detail": "Both academic years must belong to the active school and be different."}, status=400)
        target_campus = data.get("campus")
        if target_campus:
            assert_campus_allowed(request.user, target_campus)
        created = []
        skipped = []
        for item in data["students"]:
            student_id = item.get("student")
            source = Enrollment.objects.filter(
                student_id=student_id, academic_year_id=data["from_academic_year"], status="active"
            ).select_related("campus").first()
            if source is None:
                skipped.append({"student": student_id, "reason": "No active source enrollment."})
                continue
            campus_id = target_campus or source.campus_id
            assert_campus_allowed(request.user, campus_id)
            if Enrollment.objects.filter(student_id=student_id, academic_year_id=data["to_academic_year"]).exists():
                skipped.append({"student": student_id, "reason": "Already enrolled in target year."})
                continue
            target = Enrollment(
                student_id=student_id,
                academic_year_id=data["to_academic_year"],
                campus_id=campus_id,
                class_obj_id=item.get("class") or item.get("class_obj"),
                section_id=item.get("section"),
                status="active",
            )
            try:
                target.save()
            except Exception as exc:
                skipped.append({"student": student_id, "reason": str(exc)})
                continue
            source.status = "completed"
            source.save(update_fields=["status", "updated_at"])
            created.append(target.id)
        return Response({"created": created, "skipped": skipped}, status=201)

STUDENT_QUERYSET = (
    Student.objects
    .select_related("guardian")
    .prefetch_related(
        "enrollments__academic_year",
        "enrollments__campus",
        "enrollments__class_obj",
        "enrollments__section",
        "documents",
    )
)


class StudentListCreateView(generics.ListCreateAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = STUDENT_QUERYSET.order_by("first_name", "last_name")
        queryset = queryset.filter(
            enrollments__academic_year__school=self.request.institution
        )

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                queryset = queryset.filter(parent_scope_filter(user))
            else:
                queryset = queryset.filter(teacher_scope_filter(user))

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(admission_number__icontains=search)
                | Q(first_name__icontains=search)
                | Q(middle_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        gender = self.request.query_params.get("gender")

        if gender:
            queryset = queryset.filter(gender=gender)

        access = campus_access(self.request)

        if not access["global"]:
            allowed = access["allowed_ids"]
            queryset = queryset.filter(
                enrollments__campus_id__in=allowed or [-1],
                enrollments__status="active",
            )
        elif access["requested"]:
            queryset = queryset.filter(
                enrollments__campus_id=access["requested"],
                enrollments__status="active",
            )

        section = self.request.query_params.get("section")

        if section:
            queryset = queryset.filter(
                enrollments__section_id=section,
                enrollments__status="active",
            )

        class_obj = self.request.query_params.get("class_obj")

        if class_obj:
            queryset = queryset.filter(
                enrollments__class_obj_id=class_obj,
                enrollments__status="active",
            )

        return queryset


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = StudentSerializer

    def get_queryset(self):
        queryset = STUDENT_QUERYSET.filter(
            enrollments__academic_year__school=self.request.institution
        )

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                queryset = queryset.filter(parent_scope_filter(user))
            else:
                queryset = queryset.filter(teacher_scope_filter(user))

        return queryset


class StudentMyView(generics.RetrieveAPIView):
    """The student's own profile."""

    permission_classes = [IsAdminOrReadOnly]
    serializer_class = StudentSerializer

    def get_queryset(self):
        return STUDENT_QUERYSET

    def get_object(self):
        profile = get_student_profile(self.request.user)

        if profile is None:
            raise NotFound(
                "No student profile is linked to this account."
            )

        return profile


class GuardianListCreateView(generics.ListCreateAPIView):
    """Guardian registry; admins can create a parent login."""

    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GuardianCreateSerializer

        return GuardianSerializer

    def get_queryset(self):
        return Guardian.objects.filter(
            students__enrollments__academic_year__school=self.request.institution
        ).select_related("user").distinct().order_by("name")


class GuardianDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = GuardianSerializer

    def get_queryset(self):
        return Guardian.objects.filter(
            students__enrollments__academic_year__school=self.request.institution
        ).select_related("user").distinct()


class GuardianMyView(generics.RetrieveAPIView):
    """The logged-in parent's own guardian profile."""

    permission_classes = [IsAcademicMemberRole]
    serializer_class = GuardianSerializer

    def get_queryset(self):
        return Guardian.objects.select_related("user")

    def get_object(self):
        profile = get_guardian_profile(self.request.user)

        if profile is None:
            raise NotFound(
                "No guardian profile is linked to this account."
            )

        return profile


class StudentDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = StudentDocument.objects.select_related(
            "student",
            "uploaded_by",
        )

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                queryset = queryset.filter(
                    parent_scope_filter(user)
                )
            else:
                queryset = queryset.filter(
                    teacher_scope_filter(user)
                )

        student = self.request.query_params.get("student")

        if student:
            queryset = queryset.filter(student_id=student)

        document_type = self.request.query_params.get("document_type")

        if document_type:
            queryset = queryset.filter(document_type=document_type)

        return queryset

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class StudentDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = StudentDocument.objects.select_related(
            "student",
            "uploaded_by",
        )

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                queryset = queryset.filter(
                    parent_scope_filter(user)
                )
            else:
                queryset = queryset.filter(
                    teacher_scope_filter(user)
                )

        return queryset

    def perform_update(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class EnrollmentListCreateView(generics.ListCreateAPIView):
    """Assign students to a grade (class/section) for a year."""

    serializer_class = EnrollmentCreateSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = (
            Enrollment.objects
            .select_related(
                "student",
                "academic_year",
                "campus",
                "class_obj",
                "section",
            )
            .order_by("-enrollment_date", "student__first_name")
        )
        queryset = queryset.filter(
            academic_year__school=self.request.institution
        )
        queryset = campus_scoped(queryset, self.request)

        student = self.request.query_params.get("student")

        if student:
            queryset = queryset.filter(student_id=student)

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        section = self.request.query_params.get("section")

        if section:
            queryset = queryset.filter(section_id=section)

        academic_year = self.request.query_params.get("year")

        if academic_year:
            queryset = queryset.filter(
                academic_year_id=academic_year
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset


class EnrollmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = EnrollmentCreateSerializer

    def get_queryset(self):
        return campus_scoped((
            Enrollment.objects
            .select_related(
                "student",
                "academic_year",
                "campus",
                "class_obj",
                "section",
            )
        ).filter(academic_year__school=self.request.institution), self.request)


# =============================================================================
# INQUIRY VIEWS
# =============================================================================

class InquiryListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InquiryCreateSerializer
        return InquirySerializer

    def get_queryset(self):
        queryset = Inquiry.objects.select_related(
            "guardian", "campus", "academic_year", "class_obj", "assigned_to", "converted_by"
        ).filter(
            institution=self.request.institution
        )

        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        campus = self.request.query_params.get("campus")
        if campus:
            assert_campus_allowed(self.request.user, campus)
            queryset = queryset.filter(campus_id=campus)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
                | Q(inquiry_number__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(institution=self.request.institution)


class InquiryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = InquirySerializer

    def get_queryset(self):
        return Inquiry.objects.filter(institution=self.request.institution)


class InquiryConvertView(APIView):
    """Convert an inquiry to an admission application."""

    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        inquiry = get_object_or_404(
            Inquiry.objects.filter(institution=request.institution),
            pk=pk,
        )

        if inquiry.status == "converted":
            return Response({"detail": "Inquiry already converted."}, status=400)

        application_data = request.data.get("application_data", {})

        try:
            application = inquiry.convert_to_application(
                request.user,
                **application_data,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)

        return Response(
            {"application": AdmissionApplicationSerializer(application, context={"request": request}).data},
            status=201,
        )


# =============================================================================
# ACADEMIC HISTORY VIEWS
# =============================================================================

class AcademicHistoryListView(generics.ListAPIView):
    serializer_class = AcademicHistorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = AcademicHistory.objects.select_related(
            "student", "academic_year", "campus", "class_obj", "section"
        ).filter(student__institution=self.request.institution)

        student = self.request.query_params.get("student")
        if student:
            queryset = queryset.filter(student_id=student)

        academic_year = self.request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        campus = self.request.query_params.get("campus")
        if campus:
            assert_campus_allowed(self.request.user, campus)
            queryset = queryset.filter(campus_id=campus)

        final_status = self.request.query_params.get("final_status")
        if final_status:
            queryset = queryset.filter(final_status=final_status)

        return queryset


class AcademicHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AcademicHistorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return AcademicHistory.objects.filter(student__institution=self.request.institution)


# =============================================================================
# TRANSFER CERTIFICATE VIEWS
# =============================================================================

class TransferCertificateListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TransferCertificateSerializer
        return TransferCertificateSerializer

    def get_queryset(self):
        queryset = TransferCertificate.objects.select_related(
            "student", "campus", "academic_year", "class_obj", "section", "issued_by"
        ).filter(institution=self.request.institution)

        campus = self.request.query_params.get("campus")
        if campus:
            assert_campus_allowed(self.request.user, campus)
            queryset = queryset.filter(campus_id=campus)

        student = self.request.query_params.get("student")
        if student:
            queryset = queryset.filter(student_id=student)

        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def perform_create(self, serializer):
        serializer.save(institution=self.request.institution)


class TransferCertificateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransferCertificateSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return TransferCertificate.objects.filter(institution=self.request.institution)


class TransferCertificateIssueView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        certificate = get_object_or_404(
            TransferCertificate.objects.filter(institution=request.institution),
            pk=pk,
        )

        if certificate.status == "issued":
            return Response({"detail": "Certificate already issued."}, status=400)

        if certificate.status == "cancelled":
            return Response({"detail": "Cannot issue a cancelled certificate."}, status=400)

        certificate.issue(request.user)
        return Response(TransferCertificateSerializer(certificate, context={"request": request}).data)


class TransferCertificateCancelView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        certificate = get_object_or_404(
            TransferCertificate.objects.filter(institution=request.institution),
            pk=pk,
        )

        if certificate.status == "draft":
            return Response({"detail": "Cannot cancel a draft certificate. Delete it instead."}, status=400)

        certificate.cancel(request.user)
        return Response(TransferCertificateSerializer(certificate, context={"request": request}).data)


class TransferCertificateVerifyView(APIView):
    """Public endpoint to verify a transfer certificate by verification code."""

    permission_classes = []

    def get(self, request, code):
        certificate = get_object_or_404(
            TransferCertificate.objects.filter(
                institution__isnull=False,
                verification_code=code.upper(),
                status="issued",
            ),
            pk=pk,
        )
        # For public verification, return limited info
        data = {
            "certificate_number": certificate.certificate_number,
            "verification_code": certificate.verification_code,
            "student_name": certificate.full_name,
            "admission_number": certificate.admission_number,
            "date_of_birth": certificate.date_of_birth,
            "campus": certificate.campus.name,
            "academic_year": certificate.academic_year.name,
            "class_name": certificate.class_obj.name,
            "section_name": certificate.section.name,
            "admission_date": certificate.admission_date,
            "leaving_date": certificate.leaving_date,
            "reason": certificate.get_reason_display(),
            "final_grade": certificate.final_grade,
            "conduct": certificate.conduct,
            "status": certificate.status,
            "issued_at": certificate.issued_at,
            "issued_by": certificate.issued_by.get_full_name() if certificate.issued_by else None,
        }
        return Response(data)


# =============================================================================
# STUDENT 360 VIEW
# =============================================================================

class Student360View(APIView):
    """
    Comprehensive Student 360 view that aggregates data from multiple modules.
    
    Provides a complete view of a student by aggregating data from:
    - Personal details (Student model)
    - Parents/Guardians (Guardian, StudentGuardian)
    - Academic history (AcademicHistory)
    - Current enrollment (Enrollment)
    - Attendance (Attendance)
    - Exams & Results (StudentResult, PracticalResult)
    - Fees & Finance (Invoice, Payment)
    - Library (BookIssue)
    - Transport (TransportAssignment)
    - Discipline (Incident)
    - Documents (StudentDocument)
    - Certificates (TransferCertificate)
    
    Access Control:
    - Admin/Manager roles: Can view any student in their institution
    - Teachers: Can view students in their classes
    - Parents: Can view their own children
    - Students: Can view their own profile
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, student_id):
        from apps.students.models import Student
        from apps.accounts.access import assert_campus_allowed
        from apps.accounts.scopes import (
            get_student_profile, get_guardian_profile,
            is_manager, is_parent, is_student,
            parent_student_ids, parent_scope_filter,
            teacher_scope_filter,
        )
        from apps.students.serializers import Student360Serializer
        
        # Get the student
        student = get_object_or_404(
            Student.objects.select_related(
                "guardian", "primary_campus", "user", "membership", "institution"
            ).prefetch_related(
                "enrollments__campus",
                "enrollments__class_obj",
                "enrollments__section",
                "enrollments__academic_year",
                "guardian_links__guardian",
                "documents",
            ),
            pk=student_id,
            institution=request.institution,
        )
        
        # Check authorization
        user = request.user
        
        # Allow if user is the student themselves
        if student.user_id == user.id:
            pass  # Allow
        # Allow if user is a parent of the student
        elif is_parent(user) and student.id in parent_student_ids(user):
            pass  # Allow
        # Allow if user is the student themselves
        elif is_student(user) and get_student_profile(user) == student:
            pass  # Allow
        # Allow if user is a teacher of the student
        elif not is_manager(user) and hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            active_enrollment = student.enrollments.filter(status="active").first()
            if active_enrollment and teacher_can_access_student(teacher, active_enrollment):
                pass  # Allow
        # Otherwise require admin/manager role
        elif not is_manager(user):
            raise PermissionDenied("You do not have permission to view this student's profile.")
        
        # Campus access check
        active_enrollment = student.enrollments.filter(status="active").first()
        if active_enrollment:
            try:
                assert_campus_allowed(user, active_enrollment.campus_id)
            except PermissionDenied:
                raise PermissionDenied("You do not have access to this campus.")
        
        # Serialize and return
        serializer = Student360Serializer(student, context={"request": request})
        return Response(serializer.data)


def teacher_can_access_student(teacher, enrollment):
    """Check if a teacher can access a student's data."""
    from apps.teachers.models import TeacherAssignment
    
    if not enrollment:
        return False
    
    # Check if teacher is class teacher for this student's section
    return TeacherAssignment.objects.filter(
        teacher=teacher,
        class_obj=enrollment.class_obj,
        section=enrollment.section,
        role="class_teacher",
        status="active",
    ).exists()


# =============================================================================
# CAMPUS TRANSFER VIEWS
# =============================================================================

class CampusTransferListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CampusTransferCreateSerializer
        return CampusTransferSerializer
    
    def get_queryset(self):
        queryset = CampusTransfer.objects.select_related(
            "student", "from_campus", "to_campus", "academic_year",
            "requested_by", "reviewed_by", "completed_by", "reversed_by"
        ).filter(student__institution=self.request.institution)
        
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        
        campus = self.request.query_params.get("campus")
        if campus:
            assert_campus_allowed(self.request.user, campus)
            queryset = queryset.filter(Q(from_campus_id=campus) | Q(to_campus_id=campus))
        
        student = self.request.query_params.get("student")
        if student:
            queryset = queryset.filter(student_id=student)
        
        return queryset


class CampusTransferDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CampusTransferSerializer
    permission_classes = [IsAdminRole]
    
    def get_queryset(self):
        return CampusTransfer.objects.filter(
            student__institution=self.request.institution
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if instance.status == "completed":
            return Response(
                {"detail": "Cannot modify a completed transfer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        return super().update(request, *args, **partial)


class CampusTransferApproveView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            CampusTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        if transfer.status != "requested":
            return Response(
                {"detail": "Only requested transfers can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        notes = request.data.get("review_notes", "")
        transfer.approve(request.user, notes)
        
        return Response(CampusTransferSerializer(transfer, context={"request": request}).data)


class CampusTransferRejectView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            CampusTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        if transfer.status != "requested":
            return Response(
                {"detail": "Only requested transfers can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        notes = request.data.get("review_notes", "")
        transfer.reject(request.user, notes)
        
        return Response(CampusTransferSerializer(transfer, context={"request": request}).data)


class CampusTransferCompleteView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            CampusTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        if transfer.status != "approved":
            return Response(
                {"detail": "Only approved transfers can be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        transfer.complete(request.user)
        
        return Response(CampusTransferSerializer(transfer, context={"request": request}).data)


class CampusTransferCancelView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            CampusTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        if transfer.status in ["completed", "cancelled"]:
            return Response(
                {"detail": f"Cannot cancel a {transfer.status} transfer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        transfer.cancel(request.user)
        
        return Response(CampusTransferSerializer(transfer, context={"request": request}).data)


class CampusTransferReverseView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            CampusTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        reason = request.data.get("reason", "")
        transfer.reverse(request.user, reason)
        
        return Response(CampusTransferSerializer(transfer, context={"request": request}).data)


# =============================================================================
# SECTION TRANSFER VIEWS
# =============================================================================

class SectionTransferListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return SectionTransferCreateSerializer
        return SectionTransferSerializer
    
    def get_queryset(self):
        queryset = SectionTransfer.objects.select_related(
            "student", "from_section", "to_section", "academic_year",
            "requested_by", "reviewed_by", "completed_by"
        ).filter(student__institution=self.request.institution)
        
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        
        campus = self.request.query_params.get("campus")
        if campus:
            assert_campus_allowed(self.request.user, campus)
            queryset = queryset.filter(from_section__class_obj__unit__campus_id=campus)
        
        return queryset


class SectionTransferDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SectionTransferSerializer
    permission_classes = [IsAdminRole]
    
    def get_queryset(self):
        return SectionTransfer.objects.filter(
            student__institution=self.request.institution
        )


class SectionTransferApproveView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            SectionTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        if transfer.status != "requested":
            return Response(
                {"detail": "Only requested transfers can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        notes = request.data.get("review_notes", "")
        transfer.approve(request.user, notes)
        
        return Response(SectionTransferSerializer(transfer, context={"request": request}).data)


class SectionTransferRejectView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            SectionTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        if transfer.status != "requested":
            return Response(
                {"detail": "Only requested transfers can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        notes = request.data.get("review_notes", "")
        transfer.reject(request.user, notes)
        
        return Response(SectionTransferSerializer(transfer, context={"request": request}).data)


class SectionTransferCompleteView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            SectionTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        if transfer.status != "approved":
            return Response(
                {"detail": "Only approved transfers can be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        transfer.complete(request.user)
        
        return Response(SectionTransferSerializer(transfer, context={"request": request}).data)


class SectionTransferCancelView(APIView):
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        transfer = get_object_or_404(
            SectionTransfer.objects.filter(student__institution=request.institution),
            pk=pk,
        )
        
        if transfer.status in ["completed", "cancelled"]:
            return Response(
                {"detail": f"Cannot cancel a {transfer.status} transfer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        transfer.cancel(request.user)
        
        return Response(SectionTransferSerializer(transfer, context={"request": request}).data)


# =============================================================================
# ALUMNI VIEWS
# =============================================================================

class StudentGraduateView(APIView):
    """Graduate a student and create alumni record."""
    permission_classes = [IsAdminRole]
    
    @transaction.atomic
    def post(self, request, pk):
        student = get_object_or_404(
            Student.objects.filter(
                institution=request.institution,
                enrollments__academic_year__school=request.institution,
            ),
            pk=pk,
        )
        
        graduation_date = request.data.get("graduation_date")
        reason = request.data.get("reason", "Graduated")
        final_grade = request.data.get("final_grade", "")
        final_percentage = request.data.get("final_percentage")
        final_percentage = Decimal(final_percentage) if final_percentage else None
        
        alumni = student.graduate(
            request.user,
            graduation_date=graduation_date,
            reason=reason,
            final_grade=final_grade,
            final_percentage=final_percentage,
        )
        
        return Response(
            {"student": StudentSerializer(student, context={"request": request}).data,
             "alumni": StudentAlumniSerializer(alumni, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )


class StudentWithdrawView(APIView):
    """Withdraw a student."""
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        student = get_object_or_404(
            Student.objects.filter(
                institution=request.institution,
                enrollments__academic_year__school=request.institution,
            ),
            pk=pk,
        )
        
        reason = request.data.get("reason", "")
        effective_date = request.data.get("effective_date")
        
        event = student.withdraw(request.user, reason, effective_date)
        
        return Response(StudentLifecycleEventSerializer(event).data, status=status.HTTP_201_CREATED)


class StudentActivateView(APIView):
    """Reactivate a withdrawn/inactive student."""
    permission_classes = [IsAdminRole]
    
    def post(self, request, pk):
        student = get_object_or_404(
            Student.objects.filter(
                institution=request.institution,
                enrollments__academic_year__school=request.institution,
            ),
            pk=pk,
        )
        
        if student.status not in ["withdrawn", "inactive"]:
            return Response(
                {"detail": "Student is not withdrawn or inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        reason = request.data.get("reason", "Reactivated")
        effective_date = request.data.get("effective_date")
        
        event = student.activate(request.user, reason, effective_date)
        
        return Response(StudentLifecycleEventSerializer(event).data, status=status.HTTP_201_CREATED)


class StudentAlumniDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentAlumniSerializer
    permission_classes = [IsAdminRole]
    
    def get_queryset(self):
        return StudentAlumni.objects.filter(
            student__institution=self.request.institution
        ).select_related("student", "final_campus", "final_class", "final_section", "final_academic_year")