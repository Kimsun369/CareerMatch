from django.db import models


class TelegramUser(models.Model):
    """A CareerMatch user, identified solely by their Telegram account.

    No password / registration flow. Identity comes from the Telegram WebApp
    initData (verified by HMAC in users.telegram_auth) or, in local-dev mode
    only, from the X-Debug-Telegram-Id header. We deliberately store the
    minimum needed to associate preferences and saved jobs with a person.
    """

    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    first_name = models.CharField(max_length=255, blank=True, default="")
    last_name = models.CharField(max_length=255, blank=True, default="")
    username = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Telegram User"
        verbose_name_plural = "Telegram Users"

    def __str__(self) -> str:
        if self.username:
            return f"@{self.username}"
        name = " ".join(filter(None, [self.first_name, self.last_name]))
        return name or str(self.telegram_id)
