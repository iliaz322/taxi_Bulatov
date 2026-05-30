import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse


class UserFlowTests(TestCase):
    def test_user_can_register(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "newuser",
                "first_name": "Иван",
                "last_name": "Иванов",
                "email": "ivan@example.com",
                "phone": "+79990001122",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())

    def test_user_can_login(self):
        user = get_user_model().objects.create_user(
            username="client1",
            password="StrongPass123",
            phone="+79990001123",
        )
        response = self.client.post(
            reverse("users:login"),
            {"username": "client1", "password": "StrongPass123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_user_can_change_password_from_security_page(self):
        user = get_user_model().objects.create_user(
            username="client2",
            password="StrongPass123",
            phone="+79990001199",
        )
        self.client.login(username="client2", password="StrongPass123")

        response = self.client.post(
            reverse("users:security"),
            {
                "old_password": "StrongPass123",
                "new_password1": "NewStrongPass456",
                "new_password2": "NewStrongPass456",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPass456"))

    def test_user_can_upload_avatar_from_profile(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(media_root, ignore_errors=True))

        user = get_user_model().objects.create_user(
            username="client3",
            password="StrongPass123",
            phone="+79990001234",
        )
        self.client.login(username="client3", password="StrongPass123")

        avatar = SimpleUploadedFile(
            "avatar.gif",
            (
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
                b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00"
                b"\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
            ),
            content_type="image/gif",
        )

        with override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("users:profile"),
                {
                    "first_name": "Илья",
                    "last_name": "Тестов",
                    "email": "ilya@example.com",
                    "phone": "+79990001234",
                    "avatar": avatar,
                },
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(bool(user.avatar))
