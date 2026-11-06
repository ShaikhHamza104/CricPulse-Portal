import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):
    help = "Non-interactively creates or updates the administrator superuser for production and staging."

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "cricpulse@admin.com").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "kmohdhamza10@gmail.com").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "root@123").strip()

        if not username or not password:
            self.stdout.write(self.style.WARNING("Missing superuser credentials in environment; skipping."))
            return

        # Find any existing superuser by username or email
        user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).first()

        if user:
            user.username = username
            user.email = email
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' successfully updated."))
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' successfully created."))
