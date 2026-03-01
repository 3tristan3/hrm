"""OA 姓名同步服务测试。"""
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .oa_profile_sync import sync_oa_user_real_name


class OAProfileSyncTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(username="oa_sync_user", password="StrongPass#123")

    def test_sync_skipped_when_disabled(self):
        with override_settings(OA_HRM_PROFILE_SYNC_ENABLED=False):
            result = sync_oa_user_real_name(self.user, loginid="oa_sync_user")
        self.assertFalse(result)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "")

    def test_sync_once_skipped_when_first_name_exists(self):
        self.user.first_name = "已有姓名"
        self.user.save(update_fields=["first_name"])
        with override_settings(
            OA_HRM_PROFILE_SYNC_ENABLED=True,
            OA_HRM_PROFILE_SYNC_ONCE=True,
        ):
            with patch("application.oa_profile_sync.requests.post") as post_mock:
                result = sync_oa_user_real_name(self.user, loginid="oa_sync_user")
        self.assertFalse(result)
        post_mock.assert_not_called()

    @override_settings(
        OA_HRM_PROFILE_SYNC_ENABLED=True,
        OA_HRM_PROFILE_SYNC_ONCE=True,
        OA_PUSH_BASE_URL="http://oa.example.com",
        OA_PUSH_APP_ID="demo-appid",
        OA_PUSH_SECRIT="demo-secrit",
        OA_PUSH_SPK="demo-spk",
        OA_PUSH_USER_ID="3802",
        OA_PUSH_WORKFLOW_ID="1001",
    )
    def test_sync_updates_first_name_with_oa_result(self):
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.content = b"1"
        response_mock.json.return_value = {
            "code": "1",
            "data": {"dataList": [{"loginid": "oa_sync_user", "lastname": "张三"}]},
        }
        with patch(
            "application.oa_profile_sync.fetch_oa_token_value",
            return_value="token-123",
        ):
            with patch("application.oa_profile_sync.encrypt_oa_text_with_spk", return_value="enc-user-id"):
                with patch("application.oa_profile_sync.requests.post", return_value=response_mock) as post_mock:
                    result = sync_oa_user_real_name(self.user, loginid="oa_sync_user")
        self.assertTrue(result)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "张三")
        post_mock.assert_called_once()
        called_url = str(post_mock.call_args.args[0])
        self.assertTrue(called_url.endswith("/api/hrm/resful/getHrmUserInfoWithPage"))
        called_headers = post_mock.call_args.kwargs.get("headers") or {}
        self.assertEqual(called_headers.get("appid"), "demo-appid")
        self.assertEqual(called_headers.get("token"), "token-123")
        self.assertEqual(called_headers.get("userid"), "enc-user-id")
