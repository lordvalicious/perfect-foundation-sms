from rest_framework import serializers

from .models import (
    InstitutionMembership,
    RoleAssignment,
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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
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
