from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from .models import User


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with either username or email, scoped to institution."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get("email")

        identifier = username or email

        if not identifier:
            return None

        # Determine institution from request
        institution = getattr(request, "institution", None)

        # Build base queryset
        queryset = User.objects.all()

        # Filter by institution if available (non-super_admin users)
        # Super admin users have institution=None or is_superuser=True
        if institution is not None:
            queryset = queryset.filter(institution=institution)

        user = queryset.filter(
            email__iexact=identifier
        ).first()

        if user is None:
            user = queryset.filter(
                username=identifier
            ).first()

        if user is None or not user.check_password(password):
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > timezone.now():
            return None

        if not self.user_can_authenticate(user):
            return None

        return user
