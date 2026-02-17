"""地区管理后台接口测试。"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Region, UserProfile


class AdminRegionApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.base_region = Region.objects.create(name="基础地区", code="base-region")
        self.super_password = "AdminPass#123"
        self.superuser = user_model.objects.create_superuser(
            username="region_admin",
            password=self.super_password,
            email="region_admin@example.com",
        )
        self.regular_user = user_model.objects.create_user(
            username="region_operator",
            password="OperatorPass#123",
        )
        UserProfile.objects.create(
            user=self.regular_user,
            region=self.base_region,
            can_view_all=False,
        )

    def _auth(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_non_superuser_cannot_create_region(self):
        self._auth(self.regular_user)
        response = self.client.post(
            reverse("admin-regions"),
            data={"name": "华东", "code": "east", "order": 10, "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("仅系统管理员", response.json().get("error", ""))
        self.assertFalse(Region.objects.filter(code="east").exists())

    def test_superuser_can_create_region(self):
        self._auth(self.superuser)
        response = self.client.post(
            reverse("admin-regions"),
            data={"name": "华东", "code": "east", "order": 10, "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload.get("name"), "华东")
        self.assertEqual(payload.get("code"), "east")
        self.assertTrue(Region.objects.filter(code="east").exists())

    def test_non_superuser_cannot_delete_region(self):
        target = Region.objects.create(name="华南", code="south")
        self._auth(self.regular_user)
        response = self.client.delete(
            reverse("admin-region-detail", kwargs={"pk": target.id}),
            data={"password": "OperatorPass#123"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Region.objects.filter(id=target.id).exists())

    def test_superuser_delete_region_requires_password(self):
        target = Region.objects.create(name="华北", code="north")
        self._auth(self.superuser)
        response = self.client.delete(
            reverse("admin-region-detail", kwargs={"pk": target.id}),
            data={},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("密码", response.json().get("error", ""))
        self.assertTrue(Region.objects.filter(id=target.id).exists())

    def test_superuser_delete_region_rejects_wrong_password(self):
        target = Region.objects.create(name="西南", code="southwest")
        self._auth(self.superuser)
        response = self.client.delete(
            reverse("admin-region-detail", kwargs={"pk": target.id}),
            data={"password": "WrongPass#123"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("密码校验失败", response.json().get("error", ""))
        self.assertTrue(Region.objects.filter(id=target.id).exists())

    def test_superuser_delete_region_success_with_correct_password(self):
        target = Region.objects.create(name="西北", code="northwest")
        self._auth(self.superuser)
        response = self.client.delete(
            reverse("admin-region-detail", kwargs={"pk": target.id}),
            data={"password": self.super_password},
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Region.objects.filter(id=target.id).exists())

    def test_superuser_delete_region_blocked_when_protected_relations_exist(self):
        target = Region.objects.create(name="中部", code="central")
        user_model = get_user_model()
        target_user = user_model.objects.create_user(
            username="target_region_user",
            password="TargetPass#123",
        )
        UserProfile.objects.create(
            user=target_user,
            region=target,
            can_view_all=False,
        )
        self._auth(self.superuser)
        response = self.client.delete(
            reverse("admin-region-detail", kwargs={"pk": target.id}),
            data={"password": self.super_password},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("关联", response.json().get("error", ""))
        self.assertTrue(Region.objects.filter(id=target.id).exists())
