from django.contrib.auth.backends import ModelBackend

from .models import User


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with either username or email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get("email")

        identifier = username or email

        if not identifier:
            return None

        user = User.objects.filter(
            email__iexact=identifier
        ).first()

        if user is None:
            user = User.objects.filter(
                username=identifier
            ).first()

        if user is None or not user.check_password(password):
            return None

        if not self.user_can_authenticate(user):
            return None

        return user
