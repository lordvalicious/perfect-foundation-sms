from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from .models import User


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with either username or email, scoped to institution.

    Scoping sources, in order:
      * the request's resolved institution (white-label host/session);
      * an explicit ``school_code`` passed by the caller (school-aware login).

    With no scope at all the lookup is global - the caller must guarantee
    unambiguity (see ``LoginSerializer``, which refuses ambiguous logins).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        from .services import scoped_user_queryset

        email = kwargs.get("email")
        school_code = kwargs.get("school_code")

        identifier = username or email

        if not identifier:
            return None

        # Determine institution from request
        institution = getattr(request, "institution", None)

        queryset = scoped_user_queryset(
            identifier,
            school_code=school_code,
            institution=institution,
        )

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
