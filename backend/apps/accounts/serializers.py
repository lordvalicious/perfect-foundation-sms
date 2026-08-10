from rest_framework import serializers

from .models import InstitutionMembership, RoleAssignment, User


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

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "primary_role",
            "primary_institution",
            "memberships",
        ]

    def get_primary_institution(self, obj):
        institution = obj.primary_institution
        return institution.name if institution else None


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
