from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.audit.models import record_audit
from .access import (
    apply_campus_scope,
    assert_campus_allowed,
    can_manage_role,
    restrict_to_allowed_campuses,
)
from apps.accounts.permissions import (
    IsAcademicMemberRole,
    IsAdminOrReadOnly,
    IsAdminRole,
    IsStaffRole,
    IsSuperAdmin,
)
from apps.schools.serializers import SchoolSerializer
from apps.schools.models import School

from .models import (
    FailedLoginAttempt,
    InstitutionMembership,
    PasswordHistory,
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
    StaffAttendance,
    StaffAttendanceCorrection,
    StaffLeave,
    StaffProfile,
    User,
    UserPermission,
    UserSession,
)
from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PermissionSerializer,
    RolePermissionCreateSerializer,
    RolePermissionSerializer,
    StaffAttendanceCorrectionSerializer,
    StaffAttendanceSerializer,
    StaffLeaveActionSerializer,
    StaffLeaveSerializer,
    StaffProfileCRUDSerializer,
    UserPermissionCreateSerializer,
    UserPermissionSerializer,
    UserPermissionsSummarySerializer,
    UserProfileSerializer,
    UserSerializer,
)


@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"detail": "CSRF cookie set."})


# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def get_client_ip(request):
    """Extract client IP from request."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_failed_login(request, user, username_or_email):
    """Record a failed login attempt and apply lockout if threshold exceeded.

    Rapid retries of the same account from the same address inside a
    15-second window are collapsed into one record so the in-view failure
    handler and the frontend-facing ``LoginFailedView`` do not double-count
    a single bad attempt.
    """
    ip = get_client_ip(request)

    recent_cutoff = timezone.now() - timezone.timedelta(seconds=15)

    if FailedLoginAttempt.objects.filter(
        user=user,
        ip_address=ip,
        username_or_email=username_or_email,
        attempted_at__gte=recent_cutoff,
    ).exists():
        return

    user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

    FailedLoginAttempt.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent,
        username_or_email=username_or_email,
    )

    user.failed_login_attempts += 1
    user.last_failed_login_ip = ip
    user.last_failed_login_at = timezone.now()

    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = timezone.now() + timezone.timedelta(minutes=LOCKOUT_DURATION_MINUTES)

    user.save(update_fields=[
        "failed_login_attempts",
        "locked_until",
        "last_failed_login_ip",
        "last_failed_login_at",
    ])


def clear_failed_logins(user):
    """Clear failed login attempts on successful login."""
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=["failed_login_attempts", "locked_until"])


def _check_new_password(user, password):
    """Validate a new password and prevent reuse of a recent one."""
    from django.contrib.auth import hashers
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import (
        ValidationError as DjangoValidationError,
    )

    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(
            {"new_password": exc.messages}
        )

    # Reject the current password and any previously stored one. The stored
    # history entries are encoded hashes, so they are verified as encodings
    # (not as raw password candidates).
    if user.password and user.check_password(password):
        raise serializers.ValidationError(
            {"new_password": "You cannot reuse a recent password."}
        )

    for hist in user.password_history.all():
        try:
            if hashers.check_password(password, hist.password_hash):
                raise serializers.ValidationError(
                    {"new_password": "You cannot reuse a recent password."}
                )
        except (ValueError, TypeError):
            # Unparseable/stale history entry — ignore it.
            continue


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

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            identifier = str(
                request.data.get("username")
                or request.data.get("email")
                or ""
            ).strip()

            if identifier:
                user = User.objects.filter(
                    Q(email__iexact=identifier)
                    | Q(username=identifier)
                ).first()

                if user is not None:
                    record_failed_login(request, user, identifier)

            raise

        user = serializer.validated_data["user"]
        username_or_email = serializer.validated_data.get("username") or serializer.validated_data.get("email", "")

        # Check if account is locked (belt-and-suspenders, backend also checks)
        if user.locked_until and user.locked_until > timezone.now():
            lockout_remaining = int((user.locked_until - timezone.now()).total_seconds() / 60) + 1
            return Response(
                {
                    "detail": f"Account temporarily locked. Try again in {lockout_remaining} minutes.",
                    "locked_until": user.locked_until.isoformat(),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.twofa_enabled and user.twofa_secret:
            import pyotp

            code = str(request.data.get("otp") or "").strip()

            if not code or not pyotp.TOTP(user.twofa_secret).verify(
                code, valid_window=1
            ):
                record_failed_login(request, user, username_or_email)
                return Response(
                    {
                        "detail": (
                            "Enter the 6-digit code from your "
                            "authenticator app."
                        ),
                        "otp_required": True,
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        django_login(request, user)

        # Create user session record
        session_key = request.session.session_key
        if session_key:
            from django.conf import settings
            session_age = getattr(settings, "SESSION_COOKIE_AGE", 1209600)  # 2 weeks default
            UserSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                expires_at=timezone.now() + timezone.timedelta(seconds=session_age),
                is_current=True,
            )

        school_code = serializer.validated_data.get("school_code", "").strip().lower()
        memberships = user.get_active_memberships()
        membership = memberships.filter(
            institution__code=school_code
        ).first() if school_code else memberships.first()
        if membership is not None:
            request.session["active_institution_id"] = membership.institution_id

        clear_failed_logins(user)

        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=["last_login_ip"])

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
        username_or_email = request.data.get("username") or request.data.get("email", "")
        user = None

        if username_or_email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(
                models.Q(email__iexact=username_or_email) | models.Q(username=username_or_email)
            ).first()

        if user:
            record_failed_login(request, user, username_or_email)

        record_audit(
            request=request,
            action="login_failed",
            details={"username": username_or_email},
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

        # Delete current session record
        session_key = request.session.session_key
        if session_key:
            UserSession.objects.filter(
                user=request.user,
                session_key=session_key,
            ).delete()

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


class ActiveInstitutionView(APIView):
    """Read or switch the institution for the current authenticated session."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution = getattr(request, "institution", None)
        if institution is None:
            return Response({"institution": None, "roles": []})

        if request.institution_membership is not None:
            roles = request.institution_membership.role_assignments.values_list(
                "role", flat=True
            )
        else:
            roles = request.user.get_roles(institution)

        return Response(
            {
                "institution": {
                    "id": institution.id,
                    "name": institution.name,
                    "institution_type": institution.institution_type,
                },
                "roles": list(roles),
            }
        )

    def post(self, request):
        institution_id = request.data.get("institution_id")
        membership = InstitutionMembership.objects.filter(
            user=request.user,
            institution_id=institution_id,
            status="active",
        ).select_related("institution").first()

        if membership is None:
            raise PermissionDenied(
                "You do not have an active membership in this institution."
            )

        request.session["active_institution_id"] = membership.institution_id
        record_audit(
            request=request,
            action="institution_switched",
            details={"institution_id": membership.institution_id},
        )
        return Response(
            {
                "institution": {
                    "id": membership.institution_id,
                    "name": membership.institution.name,
                    "institution_type": membership.institution.institution_type,
                },
                "roles": list(
                    membership.role_assignments.values_list("role", flat=True)
                ),
            }
        )


class UserProfileView(APIView):
    """Public profile of any user (student / teacher / staff / admin)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        users = (
            User.objects.prefetch_related(
                "memberships__institution",
                "memberships__role_assignments",
            )
            .select_related("staff_profile")
        )

        if pk != request.user.pk and not request.user.is_superuser:
            institution = getattr(request, "institution", None)
            if institution is None:
                raise PermissionDenied("Select an active institution first.")
            users = users.filter(
                memberships__institution=institution,
                memberships__status="active",
            )

        user = users.filter(pk=pk).distinct().first()

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

    Sets a new password, stores password history, and invalidates the user's existing sessions.
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

        _check_new_password(user, new_password)

        # Store current password hash in history before changing
        PasswordHistory.objects.create(
            user=user,
            password_hash=user.password,
        )

        # Keep only last 5 password hashes
        old_hashes = PasswordHistory.objects.filter(user=user).order_by("-created_at")[5:]
        for old in old_hashes:
            old.delete()

        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.must_change_password = False
        user.save(update_fields=["password", "password_changed_at", "must_change_password"])

        # Invalidate all Django sessions
        for session in Session.objects.all():
            data = session.get_decoded()
            if str(data.get("_auth_user_id")) == str(user.pk):
                session.delete()

        # Invalidate all UserSession records
        UserSession.objects.filter(user=user).delete()

        record_audit(
            request=request,
            user=user,
            action="password_reset",
        )

        return Response({"detail": "Password has been reset."})


class PasswordChangeView(APIView):
    """Change password for authenticated user."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        current_password = serializer.validated_data["current_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Current password is incorrect."}
            )

        _check_new_password(user, new_password)

        # Store current password hash in history
        PasswordHistory.objects.create(
            user=user,
            password_hash=user.password,
        )

        # Keep only last 5 password hashes
        old_hashes = PasswordHistory.objects.filter(user=user).order_by("-created_at")[5:]
        for old in old_hashes:
            old.delete()

        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.must_change_password = False
        user.save(update_fields=["password", "password_changed_at", "must_change_password"])

        # Invalidate all Django sessions except current
        session_key = request.session.session_key
        for session in Session.objects.all():
            data = session.get_decoded()
            if str(data.get("_auth_user_id")) == str(user.pk):
                if session.session_key != session_key:
                    session.delete()

        # Invalidate all other UserSession records
        UserSession.objects.filter(user=user).exclude(
            session_key=session_key
        ).delete()

        # Update current session's last activity
        if session_key:
            UserSession.objects.filter(
                user=user,
                session_key=session_key,
            ).update(last_activity_at=timezone.now())

        record_audit(
            request=request,
            user=user,
            action="password_change",
        )

        return Response({"detail": "Password has been changed."})


class UserSessionSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSession
        fields = [
            "id",
            "session_key",
            "ip_address",
            "user_agent",
            "created_at",
            "last_activity_at",
            "expires_at",
            "is_current",
            "is_expired",
        ]


class SessionListView(APIView):
    """List active sessions for the current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user)
        serializer = UserSessionSerializer(sessions, many=True)
        return Response(serializer.data)


class SessionRevokeView(APIView):
    """Revoke a specific session."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):
        session = UserSession.objects.filter(
            user=request.user,
            id=session_id,
        ).first()

        if not session:
            return Response(
                {"detail": "Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Don't allow revoking current session via this endpoint
        if session.is_current:
            return Response(
                {"detail": "Cannot revoke current session. Use logout instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete Django session
        Session.objects.filter(session_key=session.session_key).delete()

        # Delete UserSession record
        session.delete()

        record_audit(
            request=request,
            action="session_revoke",
            details={"revoked_session_ip": session.ip_address},
        )

        return Response({"detail": "Session revoked."})


class SessionRevokeAllView(APIView):
    """Revoke all sessions except current."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_key = request.session.session_key

        # Delete other Django sessions
        for session in Session.objects.all():
            data = session.get_decoded()
            if str(data.get("_auth_user_id")) == str(request.user.pk):
                if session.session_key != session_key:
                    session.delete()

        # Delete other UserSession records
        UserSession.objects.filter(user=request.user).exclude(
            session_key=session_key
        ).delete()

        record_audit(
            request=request,
            action="session_revoke_all",
        )

        return Response({"detail": "All other sessions revoked."})


class AccountLockoutStatusView(APIView):
    """Check if account is locked and remaining lockout time."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.locked_until and user.locked_until > timezone.now():
            remaining = int((user.locked_until - timezone.now()).total_seconds() / 60) + 1
            return Response({
                "locked": True,
                "locked_until": user.locked_until.isoformat(),
                "remaining_minutes": remaining,
                "failed_attempts": user.failed_login_attempts,
            })
        return Response({
            "locked": False,
            "failed_attempts": user.failed_login_attempts,
        })


class AdminUnlockAccountView(APIView):
    """Admin endpoint to unlock a user account."""

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        # Check if user has admin role
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=["failed_login_attempts", "locked_until"])

        # Clear failed login attempts
        user.failed_login_records.all().delete()

        record_audit(
            request=request,
            action="account_unlock",
            details={"unlocked_user": user.username},
        )

        return Response({"detail": "Account unlocked."})


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

        queryset = restrict_to_allowed_campuses(
            queryset,
            self.request.user,
            "primary_campus_id",
        )

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


class StaffAttendanceListCreateView(generics.ListCreateAPIView):
    serializer_class = StaffAttendanceSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = StaffAttendance.objects.select_related(
            "staff",
            "staff__primary_campus",
            "marked_by",
        )

        staff = self.request.query_params.get("staff")

        if staff:
            queryset = queryset.filter(staff_id=staff)

        status_param = self.request.query_params.get("status")

        if status_param:
            queryset = queryset.filter(status=status_param)

        date = self.request.query_params.get("date")

        if date:
            queryset = queryset.filter(date=date)

        queryset = apply_campus_scope(
            queryset,
            self.request,
            campus_field="staff__primary_campus_id",
            institution_field="institution_id",
        )

        return queryset

    def perform_create(self, serializer):
        institution = getattr(self.request, "institution", None)
        staff = serializer.validated_data.get("staff")

        if staff is not None and staff.primary_campus_id:
            assert_campus_allowed(self.request.user, staff.primary_campus_id)

        serializer.save(
            marked_by=self.request.user,
            institution=institution,
        )


class StaffAttendanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StaffAttendanceSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = StaffAttendance.objects.select_related(
            "staff",
            "staff__primary_campus",
            "marked_by",
        )

        queryset = apply_campus_scope(
            queryset,
            self.request,
            campus_field="staff__primary_campus_id",
            institution_field="institution_id",
        )

        return queryset

    def perform_update(self, serializer):
        serializer.save(marked_by=self.request.user)


class StaffAttendanceCorrectionView(APIView):
    """
    Correct a staff attendance record with a reason.

    Body::

        {
          "to_status": "present"|"absent"|"late"|"half_day"|"leave",
          "to_check_in": "08:00:00",
          "to_check_out": "16:00:00",
          "reason": "Manual correction by admin"
        }

    The previous values (status, check-in, check-out) are preserved in a
    StaffAttendanceCorrection record for an immutable audit trail.
    """

    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        user = request.user
        attendance = StaffAttendance.objects.select_related(
            "staff",
            "staff__primary_campus",
        ).filter(pk=pk)

        attendance = apply_campus_scope(
            attendance,
            request,
            campus_field="staff__primary_campus_id",
            institution_field="institution_id",
        ).first()

        if attendance is None:
            raise NotFound("Attendance record not found for your scope.")

        to_status = request.data.get("to_status")
        reason = request.data.get("reason", "")

        valid_statuses = dict(StaffAttendance.STATUS_CHOICES)
        if to_status not in valid_statuses:
            return Response(
                {"detail": "Invalid status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        to_check_in = _parse_time(request.data.get("to_check_in"))
        to_check_out = _parse_time(request.data.get("to_check_out"))

        StaffAttendanceCorrection.objects.create(
            attendance=attendance,
            staff=attendance.staff,
            institution=attendance.institution
            if attendance.institution_id else getattr(request, "institution", None),
            from_status=attendance.status,
            to_status=to_status,
            from_check_in=attendance.check_in,
            to_check_in=to_check_in,
            from_check_out=attendance.check_out,
            to_check_out=to_check_out,
            reason=reason,
            corrected_by=user,
        )

        attendance.status = to_status
        attendance.check_in = to_check_in if to_check_in is not None else attendance.check_in
        attendance.check_out = to_check_out if to_check_out is not None else attendance.check_out
        attendance.notes = reason or attendance.notes
        attendance.save(
            update_fields=[
                "status",
                "check_in",
                "check_out",
                "notes",
                "updated_at",
            ]
        )

        record_audit(
            request=request,
            action="update",
            model_name="StaffAttendance",
            object_id=str(attendance.pk),
            object_repr=(
                f"Corrected staff attendance for "
                f"{attendance.staff} on {attendance.date}"
            ),
            details={"from_status": None, "to_status": to_status},
        )

        return Response(
            StaffAttendanceSerializer(attendance).data
        )


class StaffAttendanceCorrectionListView(APIView):
    """
    List the immutable correction history for a staff attendance record or
    a staff member.

        GET /api/staff/attendance/corrections/?attendance=1
        GET /api/staff/attendance/corrections/?staff=5
    """

    permission_classes = [IsStaffRole]

    def get(self, request):
        queryset = StaffAttendanceCorrection.objects.select_related(
            "staff",
            "corrected_by",
            "attendance",
        )

        staff = request.query_params.get("staff")
        if staff:
            queryset = queryset.filter(staff_id=staff)

        attendance = request.query_params.get("attendance")
        if attendance:
            queryset = queryset.filter(attendance_id=attendance)

        queryset = apply_campus_scope(
            queryset,
            request,
            campus_field="staff__primary_campus_id",
            institution_field="institution_id",
        ).order_by("-corrected_at")

        return Response(
            StaffAttendanceCorrectionSerializer(queryset, many=True).data
        )


def _parse_time(value):
    """Parse an ISO time string (HH:MM:SS) into a time, or None."""
    from datetime import datetime, time

    if not value:
        return None
    try:
        if isinstance(value, time):
            return value
        return datetime.strptime(value, "%H:%M:%S").time()
    except (TypeError, ValueError):
        return None


class StaffLeaveListCreateView(generics.ListCreateAPIView):
    serializer_class = StaffLeaveSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = StaffLeave.objects.select_related(
            "staff",
            "reviewed_by",
        )

        user = self.request.user

        if not user.has_any_role(
            ["super_admin", "admin", "principal", "hr"]
        ):
            profile = getattr(user, "staff_profile", None)

            if profile is not None:
                queryset = queryset.filter(staff=profile)
            else:
                return queryset.none()

        staff = self.request.query_params.get("staff")

        if staff:
            queryset = queryset.filter(staff_id=staff)

        status_param = self.request.query_params.get("status")

        if status_param:
            queryset = queryset.filter(status=status_param)

        leave_type = self.request.query_params.get("leave_type")

        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        staff = getattr(user, "staff_profile", None)

        if staff is None:
            raise NotFound(
                "No staff profile is linked to this account."
            )

        serializer.save(staff=staff)


class StaffLeaveDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StaffLeaveSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = StaffLeave.objects.select_related(
            "staff",
            "reviewed_by",
        )

        user = self.request.user

        if not user.has_any_role(
            ["super_admin", "admin", "principal", "hr"]
        ):
            profile = getattr(user, "staff_profile", None)

            if profile is not None:
                queryset = queryset.filter(staff=profile)
            else:
                return queryset.none()

        return queryset


class StaffLeaveActionView(generics.GenericAPIView):
    """HR approves or rejects a staff leave request."""

    serializer_class = StaffLeaveActionSerializer
    permission_classes = [IsStaffRole]

    def post(self, request, pk):
        reviewer_roles = [
            "super_admin",
            "admin",
            "principal",
            "vice_principal",
            "campus_admin",
            "hr",
        ]

        if not request.user.has_any_role(reviewer_roles):
            raise PermissionDenied(
                "Only HR / administrators can review leave requests."
            )

        leave = (
            StaffLeave.objects
            .select_related("staff")
            .filter(pk=pk)
            .first()
        )

        if leave is None:
            return Response(
                {"detail": "Leave request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        review_notes = serializer.validated_data.get("review_notes", "")

        leave.status = (
            "approved" if action == "approve" else "rejected"
        )
        leave.reviewed_by = request.user
        leave.review_notes = review_notes
        leave.save()

        record_audit(
            request=request,
            action="staff_leave_" + action,
            model_name="StaffLeave",
            object_id=str(leave.pk),
            object_repr=str(leave),
            details={
                "staff": leave.staff.employee_number,
                "leave_type": leave.leave_type,
                "start_date": str(leave.start_date),
                "end_date": str(leave.end_date),
            },
        )

        return Response(
            StaffLeaveSerializer(leave).data
        )


# =============================================================================
# PERMISSION MANAGEMENT VIEWS
# =============================================================================

class PermissionListView(APIView):
    """List all available permissions."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Only admins can view permissions
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        permissions = Permission.objects.all().order_by("category", "action", "codename")
        
        # Group by category
        grouped = {}
        for perm in permissions:
            if perm.category not in grouped:
                grouped[perm.category] = []
            grouped[perm.category].append(PermissionSerializer(perm).data)
        
        return Response(grouped)


class PermissionDetailView(APIView):
    """Get a single permission."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        perm = Permission.objects.filter(pk=pk).first()
        if not perm:
            return Response(
                {"detail": "Permission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        return Response(PermissionSerializer(perm).data)


class RolePermissionListView(APIView):
    """List role permissions for the current institution."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        institution = getattr(request, "institution", None)
        if not institution:
            return Response(
                {"detail": "No active institution selected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Only admins can view role permissions
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        role_perms = RolePermission.objects.filter(
            institution=institution
        ).select_related("permission").order_by("role", "permission__category", "permission__action")
        
        # Group by role
        grouped = {}
        for rp in role_perms:
            if rp.role not in grouped:
                grouped[rp.role] = []
            grouped[rp.role].append(RolePermissionSerializer(rp).data)
        
        return Response(grouped)


class RolePermissionCreateView(APIView):
    """Assign a permission to a role for the current institution."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        institution = getattr(request, "institution", None)
        if not institution:
            return Response(
                {"detail": "No active institution selected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Only super_admin, admin, principal can assign role permissions
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = RolePermissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Escalation guard: you may only manage permissions for roles ranked
        # strictly below your own (prevents granting your-own/higher powers).
        if not can_manage_role(request.user, serializer.validated_data["role"]):
            raise PermissionDenied(
                "You cannot assign permissions to a role at or above your own level."
            )

        # Set institution from request
        role_perm = serializer.save(institution=institution, granted_by=request.user)
        
        record_audit(
            request=request,
            action="role_permission_assign",
            model_name="RolePermission",
            object_id=str(role_perm.pk),
            object_repr=str(role_perm),
            details={
                "role": role_perm.role,
                "permission": role_perm.permission.codename,
            },
        )
        
        return Response(
            RolePermissionSerializer(role_perm).data,
            status=status.HTTP_201_CREATED,
        )


class RolePermissionDeleteView(APIView):
    """Remove a permission from a role."""
    
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        institution = getattr(request, "institution", None)
        if not institution:
            return Response(
                {"detail": "No active institution selected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        role_perm = RolePermission.objects.filter(
            pk=pk,
            institution=institution,
        ).first()
        
        if not role_perm:
            return Response(
                {"detail": "Role permission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Escalation guard: only a higher-ranked role manager may alter this.
        if not can_manage_role(request.user, role_perm.role):
            raise PermissionDenied(
                "You cannot modify permissions for a role at or above your own level."
            )

        # Prevent deleting system permissions
        if role_perm.permission.is_system:
            return Response(
                {"detail": "Cannot remove system permission from role."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        role_perm.delete()
        
        record_audit(
            request=request,
            action="role_permission_remove",
            model_name="RolePermission",
            object_id=str(pk),
            details={
                "role": role_perm.role,
                "permission": role_perm.permission.codename,
            },
        )
        
        return Response({"detail": "Permission removed from role."})


class UserPermissionListView(APIView):
    """List user-specific permissions for the current institution."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        institution = getattr(request, "institution", None)
        if not institution:
            return Response(
                {"detail": "No active institution selected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        user_perms = UserPermission.objects.filter(
            institution=institution
        ).select_related("permission", "user", "granted_by").order_by("-granted_at")
        
        return Response(UserPermissionSerializer(user_perms, many=True).data)


class UserPermissionCreateView(APIView):
    """Grant or deny a permission to a specific user."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        institution = getattr(request, "institution", None)
        if not institution:
            return Response(
                {"detail": "No active institution selected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = UserPermissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Escalation guards: no self-granting and no managing equal/higher roles.
        target_user = serializer.validated_data["user"]
        if target_user.pk == request.user.pk:
            raise PermissionDenied("You cannot grant or modify your own permissions.")
        if not can_manage_role(request.user, target_user.primary_role or Role.STUDENT):
            raise PermissionDenied(
                "You cannot manage permissions for a user with a role at or "
                "above your own level."
            )

        user_perm = serializer.save(
            institution=institution,
            granted_by=request.user,
        )
        
        record_audit(
            request=request,
            action="user_permission_grant" if user_perm.effect == "allow" else "user_permission_deny",
            model_name="UserPermission",
            object_id=str(user_perm.pk),
            object_repr=str(user_perm),
            details={
                "user": user_perm.user.username,
                "permission": user_perm.permission.codename,
                "effect": user_perm.effect,
            },
        )
        
        return Response(
            UserPermissionSerializer(user_perm).data,
            status=status.HTTP_201_CREATED,
        )


class UserPermissionDeleteView(APIView):
    """Remove a user-specific permission."""
    
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        institution = getattr(request, "institution", None)
        if not institution:
            return Response(
                {"detail": "No active institution selected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not request.user.has_any_role(["super_admin", "admin", "principal"]):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        user_perm = UserPermission.objects.filter(
            pk=pk,
            institution=institution,
        ).first()
        
        if not user_perm:
            return Response(
                {"detail": "User permission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Escalation guard: you may only revoke permissions from lower-ranked users.
        if (
            user_perm.user_id != request.user.pk
            and not can_manage_role(
                request.user, user_perm.user.primary_role or Role.STUDENT
            )
        ):
            raise PermissionDenied(
                "You cannot manage permissions for a user with a role at or "
                "above your own level."
            )

        user_perm.delete()
        
        record_audit(
            request=request,
            action="user_permission_remove",
            model_name="UserPermission",
            object_id=str(pk),
            details={
                "user": user_perm.user.username,
                "permission": user_perm.permission.codename,
            },
        )
        
        return Response({"detail": "User permission removed."})


class UserPermissionsSummaryView(APIView):
    """Get a summary of a user's effective permissions in the current institution."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        institution = getattr(request, "institution", None)
        if not institution:
            return Response(
                {"detail": "No active institution selected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Users can view their own permissions; admins can view anyone's
        if request.user.pk != user_id and not request.user.has_any_role(
            ["super_admin", "admin", "principal"]
        ):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check user has membership in this institution
        if not user.memberships.filter(institution=institution, status="active").exists():
            return Response(
                {"detail": "User is not a member of this institution."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Get role-based permissions
        memberships = user.get_active_memberships().filter(institution=institution)
        role_names = RoleAssignment.objects.filter(
            membership__in=memberships
        ).values_list("role", flat=True).distinct()
        
        role_perms = RolePermission.objects.filter(
            role__in=role_names,
            institution=institution,
        ).select_related("permission") if role_names else []
        
        # Get user-specific allow permissions
        allow_perms = user.custom_user_permissions.filter(
            institution=institution,
            effect="allow",
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).select_related("permission")
        
        # Get user-specific deny permissions
        deny_perms = user.custom_user_permissions.filter(
            institution=institution,
            effect="deny",
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).select_related("permission")
        
        # Effective permissions
        effective = user.get_permissions(institution)
        
        return Response(UserPermissionsSummarySerializer({
            "user_id": user.pk,
            "username": user.username,
            "institution_id": institution.pk,
            "institution_name": institution.name,
            "role_permissions": [
                {
                    "role": rp.role,
                    "permission": rp.permission.codename,
                    "permission_name": rp.permission.name,
                    "granted_at": rp.granted_at,
                } for rp in role_perms
            ],
            "user_allow_permissions": [
                {
                    "permission": up.permission.codename,
                    "permission_name": up.permission.name,
                    "reason": up.reason,
                    "granted_at": up.granted_at,
                    "expires_at": up.expires_at,
                } for up in allow_perms
            ],
            "user_deny_permissions": [
                {
                    "permission": up.permission.codename,
                    "permission_name": up.permission.name,
                    "reason": up.reason,
                    "granted_at": up.granted_at,
                    "expires_at": up.expires_at,
                } for up in deny_perms
            ],
            "effective_permissions": sorted(list(effective)),
        }).data)

# =============================================================================
# SUPER ADMIN SCHOOL MANAGEMENT
# =============================================================================

class SuperAdminSchoolCreateView(APIView):
    """
    Super Admin endpoint to create a new school with an admin user.
    
    POST /api/super-admin/schools/
    {
        "name": "Lahore School",
        "code": "LHR-001",  // optional, auto-generated if not provided
        "institution_type": "school",
        "timezone": "Asia/Karachi",
        "currency": "PKR",
        "address": "123 Main St, Lahore",
        "city": "Lahore",
        "admin_username": "admin",  // optional, auto-generated if not provided
        "admin_password": "TempPass123!",  // optional, auto-generated if not provided
        "admin_email": "admin@lahoreschool.edu",
        "admin_first_name": "John",
        "admin_last_name": "Doe",
        "admin_phone": "+923001234567"
    }
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = SchoolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school = serializer.save()

        # Create admin user
        admin_data = {
            "username": request.data.get("admin_username") or f"admin-{school.code.lower()}",
            "email": request.data.get("admin_email"),
            "first_name": request.data.get("admin_first_name", "Admin"),
            "last_name": request.data.get("admin_last_name", school.name),
            "phone": request.data.get("admin_phone", ""),
        }
        password = request.data.get("admin_password") or User.objects.make_random_password(length=12)

        admin_user = User.objects.create_user(
            username=admin_data["username"],
            email=admin_data["email"],
            password=password,
            first_name=admin_data["first_name"],
            last_name=admin_data["last_name"],
            phone=admin_data["phone"],
            institution=school,
            is_active=True,
        )

        # Create institution membership with admin role
        membership = InstitutionMembership.objects.create(
            user=admin_user,
            institution=school,
            status="active",
        )
        RoleAssignment.objects.create(
            membership=membership,
            role=Role.ADMIN,
        )

        # Generate credentials response
        credentials = {
            "username": admin_user.username,
            "password": password,
            "school_code": school.code,
            "school_name": school.name,
        }

        record_audit(
            request=request,
            action="school_create",
            model_name="School",
            object_id=str(school.pk),
            object_repr=school.name,
            details={
                "school_code": school.code,
                "admin_username": admin_user.username,
            },
        )

        return Response({
            "school": SchoolSerializer(school).data,
            "admin_credentials": credentials,
            "message": "School and admin user created successfully. Save the credentials securely.",
        }, status=status.HTTP_201_CREATED)


class SuperAdminSchoolListView(APIView):
    """List all schools for Super Admin."""
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        schools = School.objects.all().order_by("-created_at")
        return Response(SchoolSerializer(schools, many=True).data)


class SuperAdminSchoolSwitchView(APIView):
    """
    Super Admin endpoint to switch active institution.
    
    POST /api/super-admin/switch/
    {
        "institution_id": 1
    }
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        institution_id = request.data.get("institution_id")
        if not institution_id:
            return Response(
                {"detail": "institution_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        school = School.objects.filter(pk=institution_id, status="active").first()
        if not school:
            return Response(
                {"detail": "School not found or inactive."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update session
        request.session["active_institution_id"] = school.id

        record_audit(
            request=request,
            action="institution_switched",
            details={"institution_id": school.id, "institution_name": school.name},
        )

        return Response({
            "institution": {
                "id": school.id,
                "name": school.name,
                "code": school.code,
            },
            "message": f"Switched to {school.name}",
        })
