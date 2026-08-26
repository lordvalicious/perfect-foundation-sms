from django.db import IntegrityError
from django.utils.crypto import get_random_string
from rest_framework import serializers

from .models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffAttendance,
    StaffLeave,
    StaffProfile,
    User,
)


class RoleAssignmentSerializer(serializers.ModelSerializer):
    role_label = serializers.CharField(
        source="get_role_display",
        read_only=True,
    )

    class Meta:
        model = RoleAssignment
        fields = ["role", "role_label"]


class InstitutionMembershipSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(
        source="institution.name",
        read_only=True,
    )
    roles = RoleAssignmentSerializer(
        source="role_assignments",
        many=True,
        read_only=True,
    )

    class Meta:
        model = InstitutionMembership
        fields = [
            "id",
            "institution",
            "institution_name",
            "status",
            "joined_at",
            "roles",
        ]


class UserSerializer(serializers.ModelSerializer):
    memberships = InstitutionMembershipSerializer(
        many=True,
        read_only=True,
    )
    primary_role = serializers.CharField(
        read_only=True,
    )
    primary_institution = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    student_profile_id = serializers.SerializerMethodField()
    teacher_profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "first_name",
            "last_name",
            "photo",
            "photo_url",
            "is_staff",
            "is_superuser",
            "primary_role",
            "primary_institution",
            "student_profile_id",
            "teacher_profile_id",
            "memberships",
        ]

    def get_primary_institution(self, obj):
        institution = obj.primary_institution
        return institution.name if institution else None

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            url = obj.photo.url
            return request.build_absolute_uri(url) if request else url

        return None

    def get_student_profile_id(self, obj):
        profile = getattr(obj, "student_profile", None)
        return profile.id if profile else None

    def get_teacher_profile_id(self, obj):
        profile = getattr(obj, "teacher_profile", None)
        return profile.id if profile else None


class StaffProfileSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            "id",
            "employee_number",
            "designation",
            "department",
            "joining_date",
            "status",
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


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    primary_role = serializers.CharField(read_only=True)
    primary_institution = serializers.SerializerMethodField()
    staff_profile = StaffProfileSerializer(read_only=True)
    memberships = InstitutionMembershipSerializer(
        many=True,
        read_only=True,
    )
    student_profile_id = serializers.SerializerMethodField()
    teacher_profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "email",
            "phone",
            "photo_url",
            "primary_role",
            "primary_institution",
            "staff_profile",
            "memberships",
            "student_profile_id",
            "teacher_profile_id",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            url = obj.photo.url
            return request.build_absolute_uri(url) if request else url

        staff = getattr(obj, "staff_profile", None)

        if staff and staff.photo:
            url = staff.photo.url
            return request.build_absolute_uri(url) if request else url

        return None

    def get_primary_institution(self, obj):
        institution = obj.primary_institution
        return institution.name if institution else None

    def get_student_profile_id(self, obj):
        profile = getattr(obj, "student_profile", None)
        return profile.id if profile else None

    def get_teacher_profile_id(self, obj):
        profile = getattr(obj, "teacher_profile", None)
        return profile.id if profile else None


class StaffProfileCRUDSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    photo_url = serializers.SerializerMethodField()

    create_account = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
    )

    username = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        style={"input_type": "password"},
    )

    linked_username = serializers.SerializerMethodField()

    generated_password = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            "id",
            "employee_number",
            "user",
            "membership",
            "primary_campus",
            "linked_username",
            "generated_password",
            "photo",
            "photo_url",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "date_of_birth",
            "phone",
            "email",
            "campus",
            "designation",
            "department",
            "joining_date",
            "status",
            "create_account",
            "username",
            "password",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "photo_url",
            "linked_username",
            "generated_password",
            "created_at",
            "updated_at",
        ]

    def get_full_name(self, obj):
        return obj.full_name

    def get_linked_username(self, obj):
        return obj.user.username if obj.user_id else None

    def get_generated_password(self, obj):
        return getattr(self, "_generated_password", None)

    def _build_user_account(self, staff, username, password):
        from django.contrib.auth import get_user_model

        from apps.schools.models import School

        User = get_user_model()
        base = username or staff.employee_number
        candidate = base
        counter = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base}{counter}"
            counter += 1

        email = (staff.email or "").strip()
        if not email:
            email = f"{candidate}@perfectfoundation.local"

        generated = password or get_random_string(length=12)

        user = User.objects.create_user(
            username=candidate,
            email=email,
            password=generated,
            first_name=staff.first_name,
            last_name=staff.last_name,
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
                role=Role.STAFF,
            )

        return user, generated

    def create(self, validated_data):
        create_account = bool(validated_data.pop("create_account", False))
        username = validated_data.pop("username", "") or None
        password = validated_data.pop("password", "") or None

        staff = StaffProfile(**validated_data)
        try:
            staff.save()
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "employee_number": [
                        "A staff member with this employee number already exists."
                    ]
                }
            )

        if create_account:
            try:
                user, generated = self._build_user_account(staff, username, password)
            except IntegrityError:
                staff.delete()
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            "Could not create the login account: the username or "
                            "email is already in use."
                        ]
                    }
                )

            staff.user = user
            staff.save(update_fields=["user"])
            self._generated_password = generated

        return staff

    def update(self, instance, validated_data):
        create_account = bool(validated_data.pop("create_account", False))
        username = validated_data.pop("username", "") or None
        password = validated_data.pop("password", "") or None

        for field, value in validated_data.items():
            setattr(instance, field, value)

        try:
            instance.save()
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "employee_number": [
                        "A staff member with this employee number already exists."
                    ]
                }
            )

        if create_account:
            if instance.user_id is None:
                try:
                    user, generated = self._build_user_account(
                        instance, username, password
                    )
                except IntegrityError:
                    raise serializers.ValidationError(
                        {
                            "non_field_errors": [
                                "Could not create the login account: the username "
                                "or email is already in use."
                            ]
                        }
                    )

                instance.user = user
                instance.save(update_fields=["user"])
                self._generated_password = generated
            else:
                user = instance.user
                user.first_name = instance.first_name
                user.last_name = instance.last_name
                if instance.email:
                    user.email = instance.email
                if password:
                    user.set_password(password)
                user.save()

        return instance

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            url = obj.photo.url
            return request.build_absolute_uri(url) if request else url

        return None


class OptionalTimeField(serializers.TimeField):
    """TimeField that maps empty strings (blank form inputs) to None."""

    def to_internal_value(self, value):
        if value in ("", None):
            return None

        return super().to_internal_value(value)


class StaffAttendanceSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(
        source="staff.full_name",
        read_only=True,
    )
    staff_employee_number = serializers.CharField(
        source="staff.employee_number",
        read_only=True,
    )
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    marked_by_name = serializers.SerializerMethodField()
    check_in = OptionalTimeField(required=False, allow_null=True)
    check_out = OptionalTimeField(required=False, allow_null=True)

    class Meta:
        model = StaffAttendance
        fields = [
            "id",
            "staff",
            "staff_name",
            "staff_employee_number",
            "date",
            "status",
            "status_label",
            "check_in",
            "check_out",
            "notes",
            "marked_by",
            "marked_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "marked_by", "created_at", "updated_at"]

    def get_marked_by_name(self, obj):
        if obj.marked_by is None:
            return None

        return (
            obj.marked_by.get_full_name()
            or obj.marked_by.username
        )


class StaffLeaveSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(
        source="staff.full_name",
        read_only=True,
    )
    staff_employee_number = serializers.CharField(
        source="staff.employee_number",
        read_only=True,
    )
    leave_type_label = serializers.CharField(
        source="get_leave_type_display",
        read_only=True,
    )
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffLeave
        fields = [
            "id",
            "staff",
            "staff_name",
            "staff_employee_number",
            "leave_type",
            "leave_type_label",
            "start_date",
            "end_date",
            "days",
            "reason",
            "status",
            "status_label",
            "reviewed_by",
            "reviewed_by_name",
            "review_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "days", "reviewed_by", "created_at", "updated_at"]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by is None:
            return None

        return (
            obj.reviewed_by.get_full_name()
            or obj.reviewed_by.username
        )


class StaffLeaveActionSerializer(serializers.Serializer):
    """Approve or reject a staff leave request."""

    action = serializers.ChoiceField(
        choices=["approve", "reject"]
    )
    review_notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    school_code = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        from django.contrib.auth import authenticate

        username = attrs.get("username")
        email = attrs.get("email")

        identifier = username or email

        if not identifier:
            raise serializers.ValidationError(
                "Username or email is required."
            )

        user = authenticate(
            request=self.context.get("request"),
            username=identifier,
            password=attrs.get("password"),
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid credentials."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account has been deactivated."
            )

        school_code = attrs.get("school_code", "").strip().lower()
        if school_code and not user.memberships.filter(
            institution__code=school_code,
            status="active",
        ).exists():
            raise serializers.ValidationError(
                "This account is not a member of the selected school."
            )

        attrs["user"] = user

        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    new_password = serializers.CharField(
        min_length=8,
        write_only=True,
        style={"input_type": "password"},
    )

    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                "The two passwords do not match."
            )

        return attrs
