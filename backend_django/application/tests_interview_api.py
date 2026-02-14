"""tests_interview_api 文件，实现对应模块能力。"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Application, InterviewCandidate, Job, OperationLog, Region, UserProfile


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

    def test_batch_add_talent_pool_moves_application_and_hides_from_application_list(self):
        job = Job.objects.create(region=self.region, title="人才库测试岗位")
        application = Application.objects.create(
            region=self.region,
            job=job,
            name="人才库候选人",
            gender="男",
            phone="13800005551",
            wechat="wechat_talent_case",
        )

        response = self.client.post(
            reverse("admin-talent-pool-candidates-batch-add"),
            data={"application_ids": [application.id]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("moved"), 1)

        candidate = InterviewCandidate.objects.get(application_id=application.id)
        self.assertEqual(candidate.status, InterviewCandidate.STATUS_COMPLETED)
        self.assertEqual(candidate.result, InterviewCandidate.RESULT_REJECT)

        list_response = self.client.get(reverse("admin-applications"))
        self.assertEqual(list_response.status_code, 200)
        app_ids = {item["id"] for item in list_response.json()}
        self.assertNotIn(application.id, app_ids)

        talent_response = self.client.get(reverse("admin-talent-pool-candidates"))
        self.assertEqual(talent_response.status_code, 200)
        talent_ids = {item["id"] for item in talent_response.json()}
        self.assertIn(candidate.id, talent_ids)

        log_response = self.client.get(
            f"{reverse('admin-operation-logs')}?application_id={application.id}"
        )
        self.assertEqual(log_response.status_code, 200)
        log_payload = log_response.json()
        self.assertIn("results", log_payload)
        actions = [item["action"] for item in log_payload["results"]]
        self.assertIn("ADD_TO_TALENT_POOL", actions)
        batch_log_response = self.client.get(reverse("admin-operation-logs"))
        self.assertEqual(batch_log_response.status_code, 200)
        batch_actions = [item["action"] for item in batch_log_response.json()["results"]]
        self.assertIn("BATCH_ADD_TO_TALENT_POOL", batch_actions)

    def test_operation_logs_are_scoped_by_region(self):
        other_region = Region.objects.create(name="外部地区", code="outside")
        OperationLog.objects.create(
            operator=self.user,
            operator_username=self.user.username,
            operator_role="regional_admin",
            operator_region_name=other_region.name,
            module="applications",
            action="ADD_TO_TALENT_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="外部地区日志",
            region=other_region,
        )
        OperationLog.objects.create(
            operator=self.user,
            operator_username=self.user.username,
            operator_role="regional_admin",
            operator_region_name=self.region.name,
            module="applications",
            action="ADD_TO_TALENT_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="本地区日志",
            region=self.region,
        )

        response = self.client.get(reverse("admin-operation-logs"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("results", payload)
        summaries = {item["summary"] for item in payload["results"]}
        self.assertIn("本地区日志", summaries)
        self.assertNotIn("外部地区日志", summaries)

    def test_operation_logs_scope_by_business_region_when_region_field_is_empty(self):
        other_region = Region.objects.create(name="跨区", code="cross-region")
        other_job = Job.objects.create(region=other_region, title="跨区岗位")
        other_application = Application.objects.create(
            region=other_region,
            job=other_job,
            name="跨区候选人",
            gender="男",
            phone="13800007771",
            wechat="wechat_cross_region",
        )
        local_job = Job.objects.create(region=self.region, title="本区岗位")
        local_application = Application.objects.create(
            region=self.region,
            job=local_job,
            name="本区候选人",
            gender="男",
            phone="13800007772",
            wechat="wechat_local_region",
        )
        OperationLog.objects.create(
            operator=self.user,
            operator_username=self.user.username,
            operator_role="regional_admin",
            operator_region_name=self.region.name,
            module="applications",
            action="ADD_TO_INTERVIEW_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="跨区业务日志",
            application=other_application,
            region=None,
        )
        local_log = OperationLog.objects.create(
            operator=self.user,
            operator_username=self.user.username,
            operator_role="regional_admin",
            operator_region_name=self.region.name,
            module="applications",
            action="ADD_TO_INTERVIEW_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="本区业务日志",
            application=local_application,
            region=None,
        )

        response = self.client.get(reverse("admin-operation-logs"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        returned_ids = {item["id"] for item in payload["results"]}
        self.assertIn(local_log.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_operation_logs_support_operator_filter(self):
        OperationLog.objects.create(
            operator=self.user,
            operator_username=self.user.username,
            operator_role="regional_admin",
            operator_region_name=self.region.name,
            module="applications",
            action="ADD_TO_TALENT_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="当前账号日志",
            region=self.region,
        )
        OperationLog.objects.create(
            operator=None,
            operator_username="another_user",
            operator_role="regional_admin",
            operator_region_name=self.region.name,
            module="applications",
            action="ADD_TO_TALENT_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="其他账号日志",
            region=self.region,
        )

        response = self.client.get(f"{reverse('admin-operation-logs')}?operator=api_tester")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("results", payload)
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["operator_username"], "api_tester")

    def test_operation_logs_reject_invalid_date_range(self):
        response = self.client.get(
            f"{reverse('admin-operation-logs')}?date_from=2026-02-10&date_to=2026-02-01"
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertIn("date_to", payload)

    def test_operation_log_meta_endpoint(self):
        response = self.client.get(reverse("admin-operation-logs-meta"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("module_labels", payload)
        self.assertIn("action_labels", payload)
        self.assertIn("result_labels", payload)
        self.assertIn("page_size_options", payload)
        self.assertIn("applications", payload["module_labels"])
        self.assertIn("ADD_TO_TALENT_POOL", payload["action_labels"])
        self.assertIn(30, payload["page_size_options"])
        self.assertEqual(payload.get("pagination_mode"), "cursor")
        self.assertEqual(payload.get("default_recent_days"), 90)

    def test_operation_log_list_uses_lightweight_payload_and_detail_endpoint(self):
        log = OperationLog.objects.create(
            operator=self.user,
            operator_username=self.user.username,
            operator_role="regional_admin",
            operator_region_name=self.region.name,
            module="applications",
            action="ADD_TO_TALENT_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="轻量日志",
            details={"k": "v"},
            request_id="req-test-1",
            region=self.region,
        )
        list_response = self.client.get(reverse("admin-operation-logs"))
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()
        self.assertIn("results", list_payload)
        self.assertTrue(list_payload["results"])
        first_row = list_payload["results"][0]
        self.assertNotIn("details", first_row)

        detail_response = self.client.get(
            reverse("admin-operation-log-detail", kwargs={"pk": log.id})
        )
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()
        self.assertIn("details", detail_payload)
        self.assertEqual(detail_payload["details"].get("k"), "v")

    def test_operation_logs_default_to_recent_window(self):
        recent = OperationLog.objects.create(
            operator=self.user,
            operator_username=self.user.username,
            operator_role="regional_admin",
            operator_region_name=self.region.name,
            module="applications",
            action="ADD_TO_TALENT_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="近期日志",
            region=self.region,
        )
        old = OperationLog.objects.create(
            operator=self.user,
            operator_username=self.user.username,
            operator_role="regional_admin",
            operator_region_name=self.region.name,
            module="applications",
            action="ADD_TO_TALENT_POOL",
            result=OperationLog.RESULT_SUCCESS,
            summary="历史日志",
            region=self.region,
        )
        old_time = timezone.now() - timedelta(days=120)
        OperationLog.objects.filter(pk=old.pk).update(created_at=old_time)

        response = self.client.get(reverse("admin-operation-logs"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        summaries = {item["summary"] for item in payload["results"]}
        self.assertIn(recent.summary, summaries)
        self.assertNotIn(old.summary, summaries)

        full_response = self.client.get(
            f"{reverse('admin-operation-logs')}?date_from=2025-01-01&date_to=2026-12-31"
        )
        self.assertEqual(full_response.status_code, 200)
        full_payload = full_response.json()
        full_summaries = {item["summary"] for item in full_payload["results"]}
        self.assertIn(old.summary, full_summaries)

    def test_batch_move_talent_pool_back_to_interview_pool(self):
        talent_candidate = self._create_candidate(
            "回流候选人",
            "13800006661",
            status=InterviewCandidate.STATUS_COMPLETED,
            result=InterviewCandidate.RESULT_REJECT,
        )
        application_id = talent_candidate.application_id

        response = self.client.post(
            reverse("admin-talent-pool-candidates-batch-to-interview"),
            data={"interview_candidate_ids": [talent_candidate.id]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("moved"), 1)

        updated = InterviewCandidate.objects.get(id=talent_candidate.id)
        self.assertEqual(updated.application_id, application_id)
        self.assertEqual(updated.status, InterviewCandidate.STATUS_PENDING)
        self.assertEqual(updated.result, "")
        self.assertEqual(updated.interview_round, 1)

        interview_response = self.client.get(reverse("admin-interview-candidates"))
        self.assertEqual(interview_response.status_code, 200)
        interview_ids = {item["id"] for item in interview_response.json()}
        self.assertIn(updated.id, interview_ids)

        talent_response = self.client.get(reverse("admin-talent-pool-candidates"))
        self.assertEqual(talent_response.status_code, 200)
        talent_ids = {item["id"] for item in talent_response.json()}
        self.assertNotIn(updated.id, talent_ids)
