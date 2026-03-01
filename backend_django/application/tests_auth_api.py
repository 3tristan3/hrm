"""认证安全相关接口测试。"""
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

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

    def test_register_creates_user_and_returns_token(self):
        username = "new_user"
        response = self.client.post(
            reverse("auth-register"),
            data={
                "username": username,
                "password": "StrongPass#456",
                "region_id": self.region.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertIn("token", payload)
        self.assertEqual(payload.get("username"), username)
        self.assertEqual(payload.get("region"), self.region.id)
        self.assertFalse(payload.get("can_view_all"))
        self.assertTrue(self.user_model.objects.filter(username=username).exists())

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


class OASSOApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user_model = get_user_model()
        self.region = Region.objects.create(name="OA登录测试地区", code="oa-sso-region")
        self.username = "oa_sso_user"
        self.password = "StrongPass#123"
        self.user = self.user_model.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_oa_entry_returns_forbidden_when_disabled(self):
        response = self.client.post(
            reverse("auth-oa-entry"),
            data={"loginid": self.username, "appid": "hrm"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload.get("error_code"), "OA_SSO_DISABLED")

    @override_settings(
        OA_SSO_ENABLED=True,
        OA_SSO_ALLOWED_APPIDS=["hrm"],
        OA_SSO_DEFAULT_NEXT_URL="/jobs",
    )
    def test_oa_entry_and_exchange_success(self):
        entry_response = self.client.post(
            reverse("auth-oa-entry"),
            data={"loginid": self.username, "appid": "hrm"},
            format="json",
        )
        self.assertEqual(entry_response.status_code, 302)
        redirect_url = entry_response.get("Location", "")
        self.assertIn("oa_ticket=", redirect_url)
        query = parse_qs(urlsplit(redirect_url).query)
        ticket = str((query.get("oa_ticket") or [""])[0])
        self.assertTrue(ticket)

        exchange_response = self.client.post(
            reverse("auth-oa-exchange"),
            data={"ticket": ticket},
            format="json",
        )
        self.assertEqual(exchange_response.status_code, 200)
        payload = exchange_response.json()
        self.assertIn("token", payload)
        self.assertEqual(payload.get("username"), self.username)
        self.assertEqual(payload.get("login_source"), "oa_sso")

        second_exchange = self.client.post(
            reverse("auth-oa-exchange"),
            data={"ticket": ticket},
            format="json",
        )
        self.assertEqual(second_exchange.status_code, 400)
        self.assertEqual(second_exchange.json().get("error_code"), "OA_SSO_TICKET_INVALID")

    @override_settings(
        OA_SSO_ENABLED=True,
        OA_SSO_ALLOWED_APPIDS=["hrm"],
        OA_SSO_ALLOWED_IPS=["10.10.10.10"],
    )
    def test_oa_entry_rejects_ip_not_allowed(self):
        response = self.client.post(
            reverse("auth-oa-entry"),
            data={"loginid": self.username, "appid": "hrm"},
            format="json",
            REMOTE_ADDR="127.0.0.1",
        )
        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload.get("error_code"), "OA_SSO_IP_FORBIDDEN")

    @override_settings(
        OA_SSO_ENABLED=True,
        OA_SSO_ALLOWED_APPIDS=["hrm"],
        OA_SSO_ALLOWED_IPS=["10.10.10.10"],
    )
    def test_oa_entry_uses_x_real_ip_over_spoofed_xff(self):
        response = self.client.post(
            reverse("auth-oa-entry"),
            data={"loginid": self.username, "appid": "hrm"},
            format="json",
            REMOTE_ADDR="8.8.8.8",
            HTTP_X_REAL_IP="8.8.8.8",
            HTTP_X_FORWARDED_FOR="10.10.10.10,8.8.8.8",
        )
        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload.get("error_code"), "OA_SSO_IP_FORBIDDEN")
