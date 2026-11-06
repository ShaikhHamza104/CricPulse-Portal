from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """
    Allows users and administrators to authenticate with either their
    username or their registered email address (case-insensitive).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get("email")
        if not username or not password:
            return None

        # Look up by either case-insensitive username or case-insensitive email
        user = User.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
