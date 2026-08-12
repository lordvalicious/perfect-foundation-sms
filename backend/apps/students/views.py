from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import NotFound

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
    parent_scope_filter,
    teacher_scope_filter,
)

from .models import (
    Guardian,
    Student,
    Enrollment,
    StudentDocument,
)
from .serializers import (
    EnrollmentCreateSerializer,
    GuardianCreateSerializer,
    GuardianSerializer,
    StudentDocumentSerializer,
    StudentSerializer,
)

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

        campus = self.request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(
                enrollments__campus_id=campus,
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
        queryset = STUDENT_QUERYSET

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
        return Guardian.objects.select_related("user").order_by("name")


class GuardianDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = GuardianSerializer

    def get_queryset(self):
        return Guardian.objects.select_related("user")


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
        return (
            Enrollment.objects
            .select_related(
                "student",
                "academic_year",
                "campus",
                "class_obj",
                "section",
            )
        )