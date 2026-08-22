from datetime import date

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import assert_campus_allowed, campus_access
from apps.accounts.permissions import (
    IsAdminOrReadOnly,
    IsAdminRole,
    IsAcademicMemberRole,
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