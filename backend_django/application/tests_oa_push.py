"""OA 推送能力测试：覆盖状态落库、成功链路与手动重发接口。"""
from __future__ import annotations

from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Application, InterviewCandidate, Job, Region, UserProfile
from .oa_push import OAPushResult, dispatch_oa_push, _TOKEN_CACHE


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class OAPushTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.region = Region.objects.create(name="OA测试区域", code="oa-test-region")
        self.job = Job.objects.create(region=self.region, title="测试岗位")
        self.user = user_model.objects.create_user(username="oa_tester", password="123456")
        UserProfile.objects.create(user=self.user, region=self.region, can_view_all=False)
        token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        _TOKEN_CACHE["token"] = ""
        _TOKEN_CACHE["expires_at"] = None

    def _create_passed_candidate(self, name: str = "候选人A") -> InterviewCandidate:
        application = Application.objects.create(
            region=self.region,
            job=self.job,
            name=name,
            gender="男",
            phone="13800009990",
            wechat=f"wx_{name}",
        )
        return InterviewCandidate.objects.create(
            application=application,
            status=InterviewCandidate.STATUS_COMPLETED,
            result=InterviewCandidate.RESULT_PASS,
            offer_status=InterviewCandidate.OFFER_STATUS_CONFIRMED,
        )

    @override_settings(OA_PUSH_ENABLED=False)
    def test_dispatch_marks_failed_when_oa_disabled(self):
        candidate = self._create_passed_candidate(name="关闭OA")
        pushed_candidate, result = dispatch_oa_push(candidate.id, is_retry=False)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "OA_DISABLED")
        self.assertEqual(pushed_candidate.oa_push_status, InterviewCandidate.OA_PUSH_STATUS_FAILED)
        self.assertEqual(pushed_candidate.oa_push_error_code, "OA_DISABLED")

    @override_settings(
        OA_PUSH_ENABLED=True,
        OA_PUSH_BASE_URL="https://oa.example.com",
        OA_PUSH_APP_ID="app-test",
        OA_PUSH_SECRIT="secret-test",
        OA_PUSH_SPK="spk-test",
        OA_PUSH_USER_ID="1001",
        OA_PUSH_WORKFLOW_ID="2001",
        OA_PUSH_MAIN_FIELD_MAPPINGS=[
            {"oa_field": "xm", "source": "application.name"},
            {"oa_field": "sjh", "source": "application.phone"},
        ],
        OA_PUSH_DETAIL_DATA_TEMPLATE=[],
        OA_PUSH_OTHER_PARAMS={},
    )
    @mock.patch("application.oa_push._encrypt_text_with_spk", return_value="encrypted")
    @mock.patch("application.oa_push.requests.post")
    def test_dispatch_success_updates_candidate_status(self, mocked_post, _mocked_encrypt):
        candidate = self._create_passed_candidate(name="推送成功")
        mocked_post.side_effect = [
            _FakeResponse({"status": True, "code": 0, "token": "token-1"}, status_code=200),
            _FakeResponse({"code": "SUCCESS", "data": {"requestid": 9527}, "errMsg": {}}, status_code=200),
        ]

        pushed_candidate, result = dispatch_oa_push(candidate.id, is_retry=False)
        self.assertTrue(result.success)
        self.assertEqual(result.request_id, "9527")
        self.assertEqual(pushed_candidate.oa_push_status, InterviewCandidate.OA_PUSH_STATUS_SUCCESS)
        self.assertEqual(pushed_candidate.oa_push_request_id, "9527")

    @override_settings(
        OA_PUSH_ENABLED=True,
        OA_PUSH_BASE_URL="https://oa.example.com",
        OA_PUSH_APP_ID="app-test",
        OA_PUSH_SECRIT="secret-test",
        OA_PUSH_SPK="spk-test",
        OA_PUSH_USER_ID="1001",
        OA_PUSH_WORKFLOW_ID="2001",
        OA_PUSH_MAIN_FIELD_MAPPINGS=[
            {"oa_field": "xm", "source": "application.name"},
            {"oa_field": "sjh", "source": "application.phone"},
        ],
        OA_PUSH_DETAIL_DATA_TEMPLATE=[],
        OA_PUSH_OTHER_PARAMS={},
    )
    @mock.patch("application.oa_push._encrypt_text_with_spk", return_value="encrypted")
    @mock.patch("application.oa_push.requests.post")
    def test_dispatch_skips_duplicate_when_already_success(self, mocked_post, _mocked_encrypt):
        candidate = self._create_passed_candidate(name="幂等候选人")
        mocked_post.side_effect = [
            _FakeResponse({"status": True, "code": 0, "token": "token-2"}, status_code=200),
            _FakeResponse({"code": "SUCCESS", "data": {"requestid": 7788}, "errMsg": {}}, status_code=200),
        ]
        first_candidate, first_result = dispatch_oa_push(candidate.id, is_retry=False)
        self.assertTrue(first_result.success)
        self.assertEqual(first_candidate.oa_push_request_id, "7788")
        first_call_count = mocked_post.call_count

        second_candidate, second_result = dispatch_oa_push(candidate.id, is_retry=True)
        self.assertTrue(second_result.success)
        self.assertEqual(second_candidate.oa_push_request_id, "7788")
        self.assertEqual(mocked_post.call_count, first_call_count)

    @mock.patch("application.api_views.interviews.hire.dispatch_oa_push")
    def test_retry_oa_push_endpoint_returns_push_result(self, mocked_dispatch):
        candidate = self._create_passed_candidate(name="接口重发")
        candidate.oa_push_status = InterviewCandidate.OA_PUSH_STATUS_FAILED
        candidate.oa_push_error_code = "OA_NETWORK_ERROR"
        candidate.oa_push_error_message = "网络超时"
        candidate.save(
            update_fields=[
                "oa_push_status",
                "oa_push_error_code",
                "oa_push_error_message",
                "updated_at",
            ]
        )
        refreshed_candidate = InterviewCandidate.objects.select_related("application").get(id=candidate.id)
        mocked_dispatch.return_value = (
            refreshed_candidate,
            OAPushResult(
                success=False,
                retryable=True,
                error_code="OA_NETWORK_ERROR",
                error_message="网络超时",
            ),
        )

        response = self.client.post(
            reverse("admin-passed-candidate-retry-oa-push", kwargs={"pk": candidate.id}),
            data={},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("message"), "重发失败")
        self.assertFalse(payload.get("oa_push", {}).get("success"))
        self.assertEqual(payload.get("oa_push", {}).get("error_code"), "OA_NETWORK_ERROR")
