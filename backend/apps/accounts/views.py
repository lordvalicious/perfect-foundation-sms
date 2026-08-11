from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.audit.models import record_audit
from apps.accounts.permissions import IsAdminOrReadOnly

from .models import Role, StaffProfile, User
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    StaffProfileCRUDSerializer,
    UserProfileSerializer,
    UserSerializer,
)


@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"detail": "CSRF cookie set."})


class LoginView(APIView):
    """Session-based login. Sets the session cookie on success."""

    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        django_login(request, user)

        record_audit(
            request=request,
            action="login",
            details={"role": user.primary_role},
        )

        return Response(
            UserSerializer(
                user,
                context={"request": request},
            ).data
        )


class LoginFailedView(APIView):
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        record_audit(
            request=request,
            action="login_failed",
            details={"username": request.data.get("username")},
        )

        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        record_audit(
            request=request,
            action="logout",
        )

        django_logout(request)

        return Response({"detail": "Logged out."})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.prefetch_related(
            "memberships__institution",
            "memberships__role_assignments",
        ).get(pk=request.user.pk)

        return Response(
            UserSerializer(
                user,
                context={"request": request},
            ).data
        )


class UserProfileView(APIView):
    """Public profile of any user (student / teacher / staff / admin)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = (
            User.objects.prefetch_related(
                "memberships__institution",
                "memberships__role_assignments",
            )
            .select_related("staff_profile")
            .filter(pk=pk)
            .first()
        )

        if user is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            UserProfileSerializer(
                user,
                context={"request": request},
            ).data
        )


class RoleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.prefetch_related(
            "memberships__institution",
            "memberships__role_assignments",
        ).get(pk=request.user.pk)

        memberships = user.get_active_memberships()

        roles = []
        all_roles = set()

        for membership in memberships:
            role_assignments = (
                membership.role_assignments.all()
            )

            member_roles = [
                {
                    "role": assignment.role,
                    "role_label": assignment.get_role_display(),
                }
                for assignment in role_assignments
            ]

            all_roles.update(
                assignment.role
                for assignment in role_assignments
            )

            roles.append(
                {
                    "membership_id": membership.id,
                    "institution": membership.institution.id,
                    "institution_name": (
                        membership.institution.name
                    ),
                    "roles": member_roles,
                }
            )

        return Response(
            {
                "memberships": roles,
                "all_roles": sorted(all_roles),
                "role_labels": [
                    {
                        "value": choice[0],
                        "label": choice[1],
                    }
                    for choice in Role.choices
                ],
            }
        )


class PasswordResetRequestView(APIView):
    """
    Request a password reset link.

    Always returns the same generic response so that
    attackers cannot use this endpoint to enumerate users.
    """

    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()

        if user is not None and user.is_active:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_path = (
                f"/reset-password/{uid}/{token}/"
            )

            origin = request.build_absolute_uri("/")

            reset_url = origin.rstrip("/") + reset_path

            send_mail(
                subject="Password reset for your account",
                message=(
                    "You are receiving this email because a password "
                    "reset was requested for your account.\n\n"
                    f"Open the link below to choose a new password:\n"
                    f"{reset_url}\n\n"
                    "If you did not request this, you can ignore this "
                    "message."
                ),
                from_email=None,
                recipient_list=[email],
            )

        return Response(
            {
                "detail": (
                    "If an account exists with that email, a password "
                    "reset link has been sent."
                )
            }
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm a password reset using the uid and token from the email.

    Sets a new password and invalidates the user's existing sessions.
    """

    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid_value = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_value)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {"token": "The reset link is invalid or has expired."}
            )

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError(
                {"token": "The reset link is invalid or has expired."}
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        for session in Session.objects.all():
            data = session.get_decoded()

            if str(data.get("_auth_user_id")) == str(user.pk):
                session.delete()

        record_audit(
            request=request,
            user=user,
            action="password_reset",
        )

        return Response({"detail": "Password has been reset."})


class StaffListCreateView(generics.ListCreateAPIView):
    serializer_class = StaffProfileCRUDSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = StaffProfile.objects.all()

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(employee_number__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
                | Q(designation__icontains=search)
                | Q(department__icontains=search)
            )

        designation = self.request.query_params.get("designation")

        if designation:
            queryset = queryset.filter(
                designation__iexact=designation
            )

        department = self.request.query_params.get("department")

        if department:
            queryset = queryset.filter(
                department__iexact=department
            )

        status_param = self.request.query_params.get("status")

        if status_param:
            queryset = queryset.filter(status=status_param)

        campus = self.request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus__iexact=campus)

        return queryset


class StaffDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StaffProfileCRUDSerializer
    permission_classes = [IsAdminOrReadOnly]
    queryset = StaffProfile.objects.all()


class StaffMyView(generics.RetrieveAPIView):
    """The logged-in staff member's own profile."""

    serializer_class = StaffProfileCRUDSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self):
        profile = getattr(self.request.user, "staff_profile", None)

        if profile is None:
            raise NotFound(
                "No staff profile is linked to this account."
            )

        return profile
