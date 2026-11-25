"""Создаёт суперпользователя Django admin (идемпотентно).

Использование:
    uv run python manage.py create_admin
    ADMIN_USERNAME=root ADMIN_PASSWORD=secret uv run python manage.py create_admin
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создаёт (или обновляет) суперпользователя для Django admin."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=None)
        parser.add_argument("--password", default=None)
        parser.add_argument("--email", default="admin@example.com")

    def handle(self, *args, **options):
        username = options["username"] or os.environ.get("ADMIN_USERNAME", "admin")
        password = options["password"] or os.environ.get("ADMIN_PASSWORD", "admin")
        email = options["email"] or os.environ.get("ADMIN_EMAIL", "admin@example.com")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username, defaults={"email": email}
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "Создан" if created else "Обновлён"
        self.stdout.write(self.style.SUCCESS(f"Администратор {action}: {username}"))
