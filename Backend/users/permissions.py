from rest_framework.permissions import BasePermission

from .models import TelegramUser


class IsTelegramUser(BasePermission):
    """Allow access only to identified Telegram users.

    When no authentication class resolves a user, DRF sets request.user to
    Django's AnonymousUser (which is truthy!), so we must check the type, not
    just truthiness.
    """

    message = (
        "Could not identify you as a Telegram user. "
        "Open this app from Telegram, or (in local development only) "
        "send an X-Debug-Telegram-Id header."
    )

    def has_permission(self, request, view) -> bool:
        return isinstance(getattr(request, "user", None), TelegramUser)
