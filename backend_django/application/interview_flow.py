"""面试流程服务层：统一管理安排、取消、结果录入的状态流转。"""

from dataclasses import dataclass
from typing import Optional

from django.utils import timezone

from .models import InterviewCandidate, InterviewRoundRecord

MAX_INTERVIEW_ROUND = 3
FINAL_RESULTS = (
    InterviewCandidate.RESULT_PASS,
    InterviewCandidate.RESULT_REJECT,
)


@dataclass
class InterviewFlowError(Exception):
    """面试流程业务异常，统一返回前端可识别的 error_code。"""

    code: str
    message: str
    status_code: int = 400
    details: Optional[dict] = None

    def to_payload(self):
        """转换为接口响应结构。"""
        payload = {
            "error": self.message,
            "error_code": self.code,
        }
        if self.details:
            payload["details"] = self.details
        return payload


def _current_round(candidate: InterviewCandidate) -> int:
    """读取当前轮次，确保最小为 1。"""
    return max(int(candidate.interview_round or 1), 1)


def _is_flow_closed(candidate: InterviewCandidate) -> bool:
    """流程已结束（已完成且结果为终态）时，禁止继续安排。"""
    return (
        candidate.status == InterviewCandidate.STATUS_COMPLETED
        and candidate.result in FINAL_RESULTS
    )


def resolve_schedule_round(candidate: InterviewCandidate) -> int:
    """根据当前状态推导本次安排应使用的轮次。"""
    current_round = _current_round(candidate)
    if candidate.status == InterviewCandidate.STATUS_SCHEDULED and candidate.interview_at:
        return current_round
    if (
        candidate.status == InterviewCandidate.STATUS_PENDING
        and candidate.result == InterviewCandidate.RESULT_NEXT_ROUND
    ):
        return min(current_round + 1, MAX_INTERVIEW_ROUND)
    return current_round


def schedule_interview(
    candidate: InterviewCandidate,
    *,
    interview_at,
    interviewer: str = "",
    interview_location: str = "",
    note: Optional[str] = None,
) -> InterviewCandidate:
    """安排或改期面试，并在需要时消费“进入下一轮”状态。"""
    if _is_flow_closed(candidate):
        raise InterviewFlowError(
            code="INTERVIEW_FLOW_CLOSED",
            message="当前面试流程已结束，无法继续安排",
        )

    consume_next_round_result = (
        candidate.status == InterviewCandidate.STATUS_PENDING
        and candidate.result == InterviewCandidate.RESULT_NEXT_ROUND
    )

    candidate.interview_round = resolve_schedule_round(candidate)
    candidate.interview_at = interview_at
    candidate.interviewer = interviewer or ""
    candidate.interview_location = interview_location or ""
    if note is not None:
        candidate.note = note

    if consume_next_round_result:
        candidate.result = ""
        candidate.score = None
        candidate.result_note = ""
        candidate.result_at = None

    candidate.status = InterviewCandidate.STATUS_SCHEDULED
    update_fields = [
        "interview_round",
        "interview_at",
        "interviewer",
        "interview_location",
        "note",
        "status",
        "updated_at",
    ]
    if consume_next_round_result:
        update_fields.extend(["result", "score", "result_note", "result_at"])
    candidate.save(update_fields=update_fields)
    return candidate


def cancel_schedule(
    candidate: InterviewCandidate,
    *,
    note: str = "",
) -> InterviewCandidate:
    """取消当前面试安排，回到待安排状态。"""
    if not candidate.interview_at and candidate.status != InterviewCandidate.STATUS_SCHEDULED:
        raise InterviewFlowError(
            code="INTERVIEW_NOT_SCHEDULED",
            message="当前未安排面试",
        )

    if note:
        candidate.note = note
    candidate.interview_at = None
    candidate.interviewer = ""
    candidate.interview_location = ""
    candidate.status = InterviewCandidate.STATUS_PENDING
    candidate.save(
        update_fields=[
            "interview_at",
            "interviewer",
            "interview_location",
            "status",
            "note",
            "updated_at",
        ]
    )
    return candidate


def record_result(
    candidate: InterviewCandidate,
    *,
    result: str,
    score=None,
    result_note: str = "",
) -> InterviewCandidate:
    """记录本轮结果并推进流程，同时落盘轮次快照。"""
    if candidate.status != InterviewCandidate.STATUS_SCHEDULED or not candidate.interview_at:
        raise InterviewFlowError(
            code="INTERVIEW_NOT_SCHEDULED_FOR_RESULT",
            message="请先安排面试后再记录结果",
        )

    current_round = _current_round(candidate)
    if result == InterviewCandidate.RESULT_NEXT_ROUND and current_round >= MAX_INTERVIEW_ROUND:
        raise InterviewFlowError(
            code="INTERVIEW_ROUND_LIMIT_REACHED",
            message="当前已是第三轮，不能再进入下一轮",
        )

    InterviewRoundRecord.objects.update_or_create(
        candidate=candidate,
        round_no=current_round,
        defaults={
            "interview_at": candidate.interview_at,
            "interviewer": candidate.interviewer,
            "score": score,
            "result": result,
            "result_note": result_note,
        },
    )

    candidate.result = result
    candidate.score = score
    candidate.result_note = result_note
    candidate.result_at = timezone.now()
    candidate.interview_at = None
    candidate.interviewer = ""
    candidate.interview_location = ""
    candidate.status = (
        InterviewCandidate.STATUS_PENDING
        if result in (InterviewCandidate.RESULT_NEXT_ROUND, InterviewCandidate.RESULT_PENDING)
        else InterviewCandidate.STATUS_COMPLETED
    )
    candidate.save(
        update_fields=[
            "result",
            "score",
            "result_note",
            "result_at",
            "interview_at",
            "interviewer",
            "interview_location",
            "status",
            "updated_at",
        ]
    )
    return candidate
