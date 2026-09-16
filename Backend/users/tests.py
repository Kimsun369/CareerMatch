from django.test import TestCase

from users.models import TelegramUser


class TelegramUserBasicTests(TestCase):
    def test_create_user_with_last_name(self):
        user = TelegramUser.objects.create(
            telegram_id=500001,
            first_name="Sok",
            last_name="Chan",
            username="sokchan",
        )
        self.assertEqual(user.last_name, "Chan")

    def test_str_with_username(self):
        user = TelegramUser(telegram_id=500002, username="khmer99")
        self.assertEqual(str(user), "@khmer99")

    def test_str_without_username(self):
        user = TelegramUser(telegram_id=500003, first_name="Dara")
        self.assertEqual(str(user), "Dara")
