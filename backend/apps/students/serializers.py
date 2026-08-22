from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import serializers

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


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = [
            "id",
            "user",
            "name",
            "relationship",
            "phone",
            "alternate_phone",
            "email",
            "address",
        ]
        read_only_fields = ["id"]


class StudentGuardianSerializer(serializers.ModelSerializer):
    guardian_name = serializers.CharField(source="guardian.name", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = StudentGuardian
        fields = [
            "id",
            "student",
            "student_name",
            "guardian",
            "guardian_name",
            "relationship",
            "is_primary",
            "can_pick_up",
            "is_emergency_contact",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdmissionApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.ReadOnlyField()
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)
    class_name = serializers.CharField(source="class_obj.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AdmissionApplication
        fields = [
            "id",
            "application_number",
            "first_name",
            "middle_name",
            "last_name",
            "applicant_name",
            "date_of_birth",
            "gender",
            "phone",
            "address",
            "guardian",
            "campus",
            "campus_name",
            "academic_year",
            "academic_year_name",
            "class_obj",
            "class_name",
            "section",
            "section_name",
            "status",
            "status_display",
            "submitted_at",
            "reviewed_at",
            "reviewed_by",
            "review_notes",
            "student",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "applicant_name",
            "submitted_at",
            "reviewed_at",
            "reviewed_by",
            "student",
            "created_at",
            "updated_at",
        ]


class StudentLifecycleEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = StudentLifecycleEvent
        fields = [
            "id",
            "student",
            "student_name",
            "event_type",
            "event_type_display",
            "effective_date",
            "reason",
            "from_campus",
            "to_campus",
            "from_enrollment",
            "to_enrollment",
            "recorded_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "student",
            "from_campus",
            "to_campus",
            "from_enrollment",
            "to_enrollment",
            "recorded_by",
            "created_at",
        ]


class PromotionSerializer(serializers.Serializer):
    from_academic_year = serializers.IntegerField()
    to_academic_year = serializers.IntegerField()
    campus = serializers.IntegerField(required=False)
    students = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )


class StudentLeaveRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = StudentLeaveRequest
        fields = [
            "id", "student", "student_name", "start_date", "end_date", "reason",
            "status", "status_display", "requested_by", "reviewed_by", "reviewed_at",
            "review_notes", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "student_name", "status", "requested_by", "reviewed_by",
            "reviewed_at", "review_notes", "created_at", "updated_at",
        ]


class GuardianCreateSerializer(serializers.ModelSerializer):
    """
    Create a guardian and optionally create or link a user account
    so they can sign in to the parent portal.
    """

    username = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Guardian
        fields = [
            "user",
            "username",
            "password",
            "name",
            "relationship",
            "phone",
            "alternate_phone",
            "email",
            "address",
        ]

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if bool(username) != bool(password):
            raise serializers.ValidationError(
                "Both username and password are required "
                "to create a parent login."
            )

        return attrs

    def create(self, validated_data):
        from django.utils.crypto import get_random_string

        from apps.accounts.models import (
            InstitutionMembership,
            Role,
            RoleAssignment,
            User,
        )
        from apps.schools.models import School

        username = validated_data.pop("username", "")
        password = validated_data.pop("password", "")
        user = validated_data.get("user")

        if username or password:
            base = username or validated_data.get("phone", "parent").strip()
            candidate = base
            counter = 1

            while User.objects.filter(username=candidate).exists():
                candidate = f"{base}{counter}"
                counter += 1

            email = validated_data.get("email", "").strip()
            if not email:
                email = f"{candidate}@perfectfoundation.local"

            generated = password or get_random_string(length=12)

            user = User.objects.create_user(
                username=candidate,
                email=email,
                password=generated,
                first_name=validated_data.get("name", ""),
            )

            school = (
                School.objects.filter(status="active").order_by("id").first()
                or School.objects.first()
            )

            if school is not None:
                membership, _ = InstitutionMembership.objects.get_or_create(
                    user=user,
                    institution=school,
                    defaults={"status": "active"},
                )
                RoleAssignment.objects.get_or_create(
                    membership=membership,
                    role=Role.PARENT,
                )

            validated_data["user"] = user
        elif user is None:
            validated_data["user"] = None

        return super().create(validated_data)


class StudentDocumentSerializer(serializers.ModelSerializer):
    document_type_label = serializers.CharField(
        source="get_document_type_display",
        read_only=True,
    )
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )

    class Meta:
        model = StudentDocument
        fields = [
            "id",
            "student",
            "student_name",
            "document_type",
            "document_type_label",
            "title",
            "file",
            "file_url",
            "notes",
            "uploaded_by",
            "uploaded_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uploaded_by",
            "created_at",
            "updated_at",
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by is None:
            return None

        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

    def get_file_url(self, obj):
        request = self.context.get("request")

        if obj.file:
            url = obj.file.url
            return request.build_absolute_uri(url) if request else url

        return None


class EnrollmentSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
    )
    class_name = serializers.CharField(
        source="class_obj.name",
        read_only=True,
    )
    section_name = serializers.CharField(
        source="section.name",
        read_only=True,
    )

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "academic_year",
            "academic_year_name",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "section",
            "section_name",
            "status",
            "enrollment_date",
        ]


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """Writable serializer for assigning a student to a grade."""

    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
    )
    class_name = serializers.CharField(
        source="class_obj.name",
        read_only=True,
    )
    section_name = serializers.CharField(
        source="section.name",
        read_only=True,
    )

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_name",
            "academic_year",
            "academic_year_name",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "section",
            "section_name",
            "status",
            "enrollment_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "enrollment_date",
            "created_at",
            "updated_at",
        ]

    def _save(self, instance):
        try:
            instance.save()
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "This student is already enrolled "
                        "for this academic year."
                    ]
                }
            )

        return instance

    def create(self, validated_data):
        return self._save(Enrollment(**validated_data))

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)

        return self._save(instance)


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    photo_url = serializers.SerializerMethodField()

    guardian_details = GuardianSerializer(
        source="guardian",
        read_only=True,
    )

    enrollments = EnrollmentSerializer(
        many=True,
        read_only=True,
    )

    documents = StudentDocumentSerializer(
        many=True,
        read_only=True,
    )

    guardian_links = StudentGuardianSerializer(
        many=True,
        read_only=True,
    )

    current_enrollment = serializers.SerializerMethodField()

    guardian_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    guardian_relationship = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    guardian_phone = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    guardian_alternate_phone = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    guardian_email = serializers.EmailField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    guardian_address = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Student
        fields = [
            "id",
            "admission_number",
            "user",
            "membership",
            "primary_campus",
            "photo",
            "photo_url",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "guardian",
            "guardian_details",
            "guardian_name",
            "guardian_relationship",
            "guardian_phone",
            "guardian_alternate_phone",
            "guardian_email",
            "guardian_address",
            "guardian_links",
            "phone",
            "address",
            "status",
            "admission_date",
            "enrollments",
            "current_enrollment",
            "documents",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "guardian",
            "full_name",
            "photo_url",
            "created_at",
            "updated_at",
        ]

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            url = obj.photo.url
            return request.build_absolute_uri(url) if request else url

        return None

    def get_current_enrollment(self, obj):
        enrollment = (
            obj.enrollments.filter(status="active")
            .select_related(
                "campus",
                "class_obj",
                "section",
                "academic_year",
            )
            .first()
        )

        if enrollment is None:
            return None

        return {
            "enrollment_id": enrollment.id,
            "campus_id": enrollment.campus_id,
            "campus_name": enrollment.campus.name,
            "class_id": enrollment.class_obj_id,
            "class_name": enrollment.class_obj.name,
            "section_id": enrollment.section_id,
            "section_name": enrollment.section.name,
            "academic_year_id": enrollment.academic_year_id,
            "academic_year_name": enrollment.academic_year.name,
        }

    def validate(self, attrs):
        creating = self.instance is None

        if creating:
            required = [
                "guardian_name",
                "guardian_relationship",
                "guardian_phone",
            ]

            for field in required:
                if not attrs.get(field):
                    raise serializers.ValidationError(
                        {field: "This field is required."}
                    )

        return attrs

    def _extract_guardian(self, attrs):
        """Pull the flat guardian_* fields out of attrs, dropping empties."""
        prefix = "guardian_"
        flat = {k: v for k, v in attrs.items() if k.startswith(prefix)}

        for key in flat:
            del attrs[key]

        mapping = {
            "guardian_name": "name",
            "guardian_relationship": "relationship",
            "guardian_phone": "phone",
            "guardian_alternate_phone": "alternate_phone",
            "guardian_email": "email",
            "guardian_address": "address",
        }

        return {
            mapping[key]: value
            for key, value in flat.items()
            if value not in (None, "")
        }

    def create(self, validated_data):
        guardian_data = self._extract_guardian(validated_data)

        guardian = Guardian.objects.create(**guardian_data)

        validated_data["guardian"] = guardian

        return super().create(validated_data)

    def update(self, instance, validated_data):
        guardian_data = self._extract_guardian(validated_data)

        if guardian_data and instance.guardian_id:
            for field, value in guardian_data.items():
                setattr(instance.guardian, field, value)

            instance.guardian.save()

        return super().update(instance, validated_data)
