"""tests_interview_api 文件，实现对应模块能力。"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Application, InterviewCandidate, Job, Region, UserProfile


class InterviewMetaApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.region = Region.objects.create(name="测试地区", code="api-test")
        self.user = user_model.objects.create_user(username="api_tester", password="123456")
        UserProfile.objects.create(user=self.user, region=self.region, can_view_all=False)
        token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_admin_interview_meta(self):
        url = reverse("admin-interview-meta")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("status_scheduled", payload)
        self.assertIn("result_next_round", payload)
        self.assertIn("final_results", payload)
        self.assertIn("max_round", payload)
        self.assertGreaterEqual(int(payload["max_round"]), 1)

    def test_result_requires_scheduled_interview_with_error_code(self):
        job = Job.objects.create(region=self.region, title="测试岗位")
        application = Application.objects.create(
            region=self.region,
            job=job,
            name="测试候选人",
            gender="男",
            phone="13800001111",
            wechat="wechat_test",
        )
        candidate = InterviewCandidate.objects.create(application=application)

        url = reverse("admin-interview-candidate-result", kwargs={"pk": candidate.id})
        response = self.client.post(
            url,
            data={"result": InterviewCandidate.RESULT_PASS, "score": 90},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload.get("error_code"), "INTERVIEW_NOT_SCHEDULED_FOR_RESULT")

    def _create_candidate(self, name, phone, *, status=None, result=None):
        job = Job.objects.create(region=self.region, title=f"{name}-岗位")
        application = Application.objects.create(
            region=self.region,
            job=job,
            name=name,
            gender="男",
            phone=phone,
            wechat=f"wechat_{name}",
        )
        kwargs = {}
        if status is not None:
            kwargs["status"] = status
        if result is not None:
            kwargs["result"] = result
        return InterviewCandidate.objects.create(application=application, **kwargs)

    def test_completed_candidates_are_hidden_from_interview_pool(self):
        pending_candidate = self._create_candidate("待安排候选人", "13800002221")
        self._create_candidate(
            "已通过候选人",
            "13800002222",
            status=InterviewCandidate.STATUS_COMPLETED,
            result=InterviewCandidate.RESULT_PASS,
        )
        self._create_candidate(
            "已淘汰候选人",
            "13800002223",
            status=InterviewCandidate.STATUS_COMPLETED,
            result=InterviewCandidate.RESULT_REJECT,
        )

        response = self.client.get(reverse("admin-interview-candidates"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        returned_ids = {item["id"] for item in payload}
        self.assertIn(pending_candidate.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_talent_pool_contains_only_rejected_candidates(self):
        reject_candidate = self._create_candidate(
            "淘汰候选人",
            "13800003331",
            status=InterviewCandidate.STATUS_COMPLETED,
            result=InterviewCandidate.RESULT_REJECT,
        )
        self._create_candidate(
            "通过候选人",
            "13800003332",
            status=InterviewCandidate.STATUS_COMPLETED,
            result=InterviewCandidate.RESULT_PASS,
        )
        self._create_candidate("流程中候选人", "13800003333")

        response = self.client.get(reverse("admin-talent-pool-candidates"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], reject_candidate.id)

    def test_talent_pool_supports_paginated_response_when_requested(self):
        self._create_candidate(
            "淘汰候选人A",
            "13800004441",
            status=InterviewCandidate.STATUS_COMPLETED,
            result=InterviewCandidate.RESULT_REJECT,
        )
        self._create_candidate(
            "淘汰候选人B",
            "13800004442",
            status=InterviewCandidate.STATUS_COMPLETED,
            result=InterviewCandidate.RESULT_REJECT,
        )

        response = self.client.get(
            f"{reverse('admin-talent-pool-candidates')}?page=1&page_size=1"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("count", payload)
        self.assertIn("results", payload)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(len(payload["results"]), 1)
