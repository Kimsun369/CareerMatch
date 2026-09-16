"""Telegram WebApp identity verification.

Real production auth:
    The frontend sends the raw ``initData`` string that Telegram's WebApp SDK
    provides (via the ``X-Telegram-Init-Data`` header). We verify its HMAC
    signature against the bot token per Telegram's official spec:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

Dev fallback:
    When ``DEBUG=True`` and no init data is supplied, requests may pass an
    ``X-Debug-Telegram-Id`` header so the app is testable in an ordinary
    browser. This path is refused when ``DEBUG=False``, so it can never
    become the production identity mechanism.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from django.conf import settings
from rest_framework import authentication, exceptions

from .models import TelegramUser


class TelegramAuthError(exceptions.AuthenticationFailed):
    pass


def verify_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict:
    """Verify a Telegram WebApp initData string and return its parsed fields.

    Raises ``TelegramAuthError`` if the signature is invalid, missing,
    or stale (older than ``max_age_seconds``).

    Algorithm per https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app:
        1. Extract and remove the ``hash`` field from the data string.
        2. Sort remaining fields alphabetically and join as ``key=value\\n...``.
        3. Compute HMAC-SHA256 of that string using the key
           HMAC-SHA256("WebAppData", bot_token).
        4. Compare (constant-time) against the received hash.
    """
    if not bot_token:
        raise TelegramAuthError(
            "TELEGRAM_BOT_TOKEN is not configured on the server; "
            "cannot verify Telegram identity."
        )

    pairs = parse_qsl(init_data, keep_blank_values=True)
    data = dict(pairs)
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise TelegramAuthError("Missing hash in Telegram init data.")

    # Build the check string: sorted key=value pairs joined by newlines.
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    # Derive the signing key: HMAC-SHA256("WebAppData", bot_token).
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    # Compute the expected hash.
    computed_hash = hmac.new(
        secret_key,
        check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise TelegramAuthError("Invalid Telegram init data signature.")

    auth_date = data.get("auth_date")
    if auth_date:
        try:
            age = time.time() - int(auth_date)
            if age > max_age_seconds:
                raise TelegramAuthError("Telegram init data has expired.")
        except ValueError:
            raise TelegramAuthError("Telegram init data has an invalid auth_date field.")

    # Decode the nested 'user' JSON object if present.
    if "user" in data:
        try:
            data["user"] = json.loads(data["user"])
        except (ValueError, TypeError):
            raise TelegramAuthError("Telegram init data has an invalid 'user' field.")

    return data


class TelegramWebAppAuthentication(authentication.BaseAuthentication):
    """Resolves the request to a TelegramUser (creating one on first visit).

    Tries in order:
    1. X-Telegram-Init-Data header  — HMAC-verified; always accepted.
    2. X-Debug-Telegram-Id header   — only honoured when DEBUG=True.

    Returns None (not an error) if neither header is present, letting
    DRF fall through to the next authentication class (if any), or
    ultimately the permission class which will reject the anonymous request.
    """

    def authenticate(self, request):
        init_data = request.headers.get("X-Telegram-Init-Data")

        if init_data:
            parsed = verify_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
            tg_user = parsed.get("user") or {}
            telegram_id = tg_user.get("id")
            if telegram_id is None:
                raise TelegramAuthError(
                    "Telegram init data did not include a user id."
                )
            user, _ = TelegramUser.objects.update_or_create(
                telegram_id=int(telegram_id),
                defaults={
                    "first_name": tg_user.get("first_name", ""),
                    "last_name": tg_user.get("last_name", ""),
                    "username": tg_user.get("username"),
                },
            )
            return (user, None)

        # ── Local/dev-only fallback ───────────────────────────────────────────
        # Accepted only when DJANGO_DEBUG=True so it cannot ever become the
        # production identity path.
        debug_id = request.headers.get("X-Debug-Telegram-Id")
        if debug_id and settings.DEBUG:
            try:
                telegram_id = int(debug_id)
            except (TypeError, ValueError):
                raise TelegramAuthError(
                    "X-Debug-Telegram-Id must be a numeric Telegram user id."
                )
            user, _ = TelegramUser.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={"first_name": "Dev User"},
            )
            return (user, None)

        return None
