"""认证安全相关接口测试。"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Region


class AuthHardeningApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user_model = get_user_model()
        self.region = Region.objects.create(name="认证测试地区", code="auth-test")
        self.username = "auth_tester"
        self.password = "StrongPass#123"
        self.user = self.user_model.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_register_requires_strong_password(self):
        response = self.client.post(
            reverse("auth-register"),
            data={
                "username": "new_user",
                "password": "12345678",
                "region_id": self.region.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertIn("details", payload)
        self.assertIn("password", payload["details"])

    def test_login_rotates_token(self):
        old_token = Token.objects.create(user=self.user)
        response = self.client.post(
            reverse("auth-login"),
            data={"username": self.username.upper(), "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("token", payload)
        self.assertNotEqual(payload["token"], old_token.key)
        self.assertFalse(Token.objects.filter(key=old_token.key).exists())
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    @override_settings(AUTH_TOKEN_TTL_HOURS=1)
    def test_me_rejects_expired_token(self):
        token = Token.objects.create(user=self.user)
        old_time = timezone.now() - timedelta(hours=2)
        Token.objects.filter(pk=token.pk).update(created=old_time)
        token.refresh_from_db()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, 401)

    def test_logout_revokes_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.post(reverse("auth-logout"), data={}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Token.objects.filter(key=token.key).exists())

        after_response = self.client.get(reverse("auth-me"))
        self.assertEqual(after_response.status_code, 401)

    def test_change_password_invalidates_current_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.post(
            reverse("auth-password"),
            data={
                "old_password": self.password,
                "new_password": "AnotherStrong#123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("force_relogin"))
        self.assertFalse(Token.objects.filter(key=token.key).exists())

        after_response = self.client.get(reverse("auth-me"))
        self.assertEqual(after_response.status_code, 401)

    @override_settings(
        AUTH_LOGIN_MAX_FAILURES=3,
        AUTH_LOGIN_LOCK_MINUTES=1,
        AUTH_LOGIN_FAILURE_WINDOW_MINUTES=60,
    )
    def test_login_is_locked_after_multiple_failures(self):
        for _ in range(2):
            response = self.client.post(
                reverse("auth-login"),
                data={"username": self.username, "password": "wrong-password"},
                format="json",
            )
            self.assertEqual(response.status_code, 400)

        locked_response = self.client.post(
            reverse("auth-login"),
            data={"username": self.username, "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(locked_response.status_code, 429)
        payload = locked_response.json()
        self.assertEqual(payload.get("error_code"), "LOGIN_LOCKED")
        self.assertGreater(int(payload.get("retry_after_seconds", 0)), 0)

    @override_settings(
        AUTH_LOGIN_RATE="2/min",
        AUTH_LOGIN_MAX_FAILURES=99,
    )
    def test_login_endpoint_is_throttled(self):
        for _ in range(2):
            response = self.client.post(
                reverse("auth-login"),
                data={"username": self.username, "password": "wrong-password"},
                format="json",
            )
            self.assertEqual(response.status_code, 400)

        throttled_response = self.client.post(
            reverse("auth-login"),
            data={"username": self.username, "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(throttled_response.status_code, 429)
