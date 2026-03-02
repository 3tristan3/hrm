"""面试流程服务测试：验证安排、取消与结果流转的状态机规则。"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .interview_flow import (
    InterviewFlowError,
    cancel_schedule,
    normalize_interviewer_decisions,
    record_result,
    schedule_interview,
)
from .models import Application, InterviewCandidate, InterviewRoundRecord, Job, Region


class InterviewFlowServiceTests(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name="测试地区", code="test-region")
        self.job = Job.objects.create(region=self.region, title="测试岗位")
        self._seq = 0

    def _create_candidate(self, **candidate_kwargs):
        self._seq += 1
        application = Application.objects.create(
            region=self.region,
            job=self.job,
            name=f"候选人{self._seq}",
            gender="男",
            phone=f"1380000{self._seq:04d}",
            wechat=f"wechat_{self._seq}",
        )
        return InterviewCandidate.objects.create(application=application, **candidate_kwargs)

    def test_schedule_first_round(self):
        candidate = self._create_candidate()
        interview_at = timezone.now() + timedelta(hours=2)

        schedule_interview(
            candidate,
            interview_at=interview_at,
            interviewer="面试官A",
            interview_location="会议室1",
            note="请准时",
        )
        candidate.refresh_from_db()

        self.assertEqual(candidate.status, InterviewCandidate.STATUS_SCHEDULED)
        self.assertEqual(candidate.interview_round, 1)
        self.assertEqual(candidate.interviewer, "面试官A")
        self.assertEqual(candidate.interviewers, ["面试官A"])
        self.assertEqual(candidate.interview_location, "会议室1")
        self.assertEqual(candidate.note, "请准时")
        self.assertIsNotNone(candidate.interview_at)

    def test_schedule_supports_multiple_interviewers(self):
        candidate = self._create_candidate()
        interview_at = timezone.now() + timedelta(hours=2)

        schedule_interview(
            candidate,
            interview_at=interview_at,
            interviewers=["面试官A", "面试官B", "面试官A"],
            interview_location="会议室2",
        )
        candidate.refresh_from_db()

        self.assertEqual(candidate.interviewer, "面试官A、面试官B")
        self.assertEqual(candidate.interviewers, ["面试官A", "面试官B"])

    def test_next_round_result_then_schedule_advances_round(self):
        candidate = self._create_candidate()
        first_interview_at = timezone.now() + timedelta(hours=2)
        second_interview_at = timezone.now() + timedelta(days=1)

        schedule_interview(candidate, interview_at=first_interview_at, interviewer="面试官A")
        record_result(
            candidate,
            result=InterviewCandidate.RESULT_NEXT_ROUND,
            interviewer_decisions=[{"interviewer": "面试官A", "decision": "pass"}],
            result_note="一面可进入二面",
        )
        candidate.refresh_from_db()
        self.assertEqual(candidate.status, InterviewCandidate.STATUS_PENDING)
        self.assertEqual(candidate.result, InterviewCandidate.RESULT_NEXT_ROUND)

        schedule_interview(candidate, interview_at=second_interview_at, interviewer="面试官B")
        candidate.refresh_from_db()
        self.assertEqual(candidate.status, InterviewCandidate.STATUS_SCHEDULED)
        self.assertEqual(candidate.interview_round, 2)
        self.assertEqual(candidate.result, "")
        self.assertIsNone(candidate.score)
        self.assertEqual(candidate.interviewer_scores, [])
        self.assertEqual(candidate.result_note, "")

    def test_record_pass_result_creates_round_record(self):
        candidate = self._create_candidate()
        interview_at = timezone.now() + timedelta(hours=2)
        schedule_interview(candidate, interview_at=interview_at, interviewer="面试官A")

        record_result(
            candidate,
            result=InterviewCandidate.RESULT_PASS,
            interviewer_decisions=[{"interviewer": "面试官A", "decision": "pass"}],
            result_note="综合能力优秀",
        )
        candidate.refresh_from_db()

        self.assertEqual(candidate.status, InterviewCandidate.STATUS_COMPLETED)
        self.assertEqual(candidate.result, InterviewCandidate.RESULT_PASS)
        self.assertIsNotNone(candidate.result_at)
        self.assertEqual(candidate.interviewer, "")
        self.assertIsNone(candidate.interview_at)

        round_record = InterviewRoundRecord.objects.get(candidate=candidate, round_no=1)
        self.assertIsNone(round_record.score)
        self.assertEqual(round_record.result, InterviewCandidate.RESULT_PASS)
        self.assertEqual(round_record.interviewer, "面试官A")
        self.assertEqual(
            round_record.interviewer_scores,
            [{"interviewer": "面试官A", "decision": "pass"}],
        )

    def test_record_pass_result_resets_offer_status_to_pending(self):
        candidate = self._create_candidate(
            offer_status=InterviewCandidate.OFFER_STATUS_REJECTED,
            is_hired=True,
            hired_at=timezone.now(),
        )
        interview_at = timezone.now() + timedelta(hours=2)
        schedule_interview(candidate, interview_at=interview_at, interviewer="面试官A")

        record_result(
            candidate,
            result=InterviewCandidate.RESULT_PASS,
            interviewer_decisions=[{"interviewer": "面试官A", "decision": "pass"}],
            result_note="通过后进入待发offer",
        )
        candidate.refresh_from_db()

        self.assertEqual(candidate.offer_status, InterviewCandidate.OFFER_STATUS_PENDING)
        self.assertFalse(candidate.is_hired)
        self.assertIsNone(candidate.hired_at)

    def test_record_pending_result_keeps_candidate_in_flow(self):
        candidate = self._create_candidate()
        interview_at = timezone.now() + timedelta(hours=2)
        schedule_interview(candidate, interview_at=interview_at, interviewer="面试官A")

        record_result(
            candidate,
            result=InterviewCandidate.RESULT_PENDING,
            interviewer_decisions=[{"interviewer": "面试官A", "decision": "pass"}],
            result_note="需要补充资料后再定",
        )
        candidate.refresh_from_db()

        self.assertEqual(candidate.status, InterviewCandidate.STATUS_PENDING)
        self.assertEqual(candidate.result, InterviewCandidate.RESULT_PENDING)
        self.assertIsNone(candidate.interview_at)
        self.assertEqual(candidate.interviewer, "")

    def test_record_result_keeps_round_interviewers_and_clears_score_fields(self):
        candidate = self._create_candidate()
        interview_at = timezone.now() + timedelta(hours=2)
        schedule_interview(
            candidate,
            interview_at=interview_at,
            interviewers=["面试官A", "面试官B"],
        )

        record_result(
            candidate,
            result=InterviewCandidate.RESULT_PASS,
            interviewer_decisions=[
                {"interviewer": "面试官A", "decision": "pass"},
                {"interviewer": "面试官B", "decision": "fail"},
            ],
            result_note="双面试官均通过",
        )
        candidate.refresh_from_db()

        self.assertEqual(candidate.result, InterviewCandidate.RESULT_PASS)
        self.assertIsNone(candidate.score)
        self.assertEqual(
            candidate.interviewer_scores,
            [
                {"interviewer": "面试官A", "decision": "pass"},
                {"interviewer": "面试官B", "decision": "fail"},
            ],
        )

        round_record = InterviewRoundRecord.objects.get(candidate=candidate, round_no=1)
        self.assertEqual(round_record.interviewers, ["面试官A", "面试官B"])
        self.assertEqual(round_record.interviewer, "面试官A、面试官B")
        self.assertIsNone(round_record.score)

    def test_record_next_round_on_round_three_should_fail(self):
        candidate = self._create_candidate(
            status=InterviewCandidate.STATUS_SCHEDULED,
            interview_round=3,
            interview_at=timezone.now() + timedelta(hours=1),
            interviewer="面试官C",
        )

        with self.assertRaises(InterviewFlowError) as ctx:
            record_result(
                candidate,
                result=InterviewCandidate.RESULT_NEXT_ROUND,
                interviewer_decisions=[{"interviewer": "面试官C", "decision": "pass"}],
            )

        self.assertEqual(ctx.exception.code, "INTERVIEW_ROUND_LIMIT_REACHED")

    def test_normalize_interviewer_decisions(self):
        self.assertEqual(
            normalize_interviewer_decisions(
                [
                    {"interviewer": "A", "decision": "pass"},
                    {"interviewer": "A", "decision": "fail"},
                    {"interviewer": "B", "decision": "fail"},
                    {"interviewer": " ", "decision": "pass"},
                ]
            ),
            [
                {"interviewer": "A", "decision": "pass"},
                {"interviewer": "B", "decision": "fail"},
            ],
        )

    def test_cancel_unscheduled_should_fail(self):
        candidate = self._create_candidate()

        with self.assertRaises(InterviewFlowError) as ctx:
            cancel_schedule(candidate)

        self.assertEqual(ctx.exception.code, "INTERVIEW_NOT_SCHEDULED")
