"""Offer 状态流转服务：统一处理状态解析、校验与状态写入。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.utils import timezone

from .models import InterviewCandidate


@dataclass
class OfferStatusTransitionError(Exception):
    """状态流转业务异常，携带统一错误描述与细节。"""

    code: str
    error: str
    details: dict[str, Any] | None = None


class OfferStatusTransitionService:
    """集中管理通过池 Offer 状态流转规则。"""

    @classmethod
    def resolve_offer_status(cls, candidate: InterviewCandidate) -> str:
        raw_status = str(candidate.offer_status or "").strip()
        if raw_status:
            return raw_status
        return (
            InterviewCandidate.OFFER_STATUS_CONFIRMED
            if candidate.is_hired
            else InterviewCandidate.OFFER_STATUS_PENDING
        )

    @classmethod
    def ensure_confirm_hire_eligible(cls, candidate: InterviewCandidate):
        if (
            candidate.status != InterviewCandidate.STATUS_COMPLETED
            or candidate.result != InterviewCandidate.RESULT_PASS
        ):
            raise OfferStatusTransitionError(
                code="invalid_candidate_state",
                error="仅支持对“已完成且通过”的候选人确认入职",
            )
        if cls.resolve_offer_status(candidate) != InterviewCandidate.OFFER_STATUS_PENDING:
            raise OfferStatusTransitionError(
                code="invalid_offer_status_for_confirm",
                error="仅支持对“待确认入职”状态候选人执行确认入职",
            )

    @classmethod
    def apply_confirm_hire(
        cls,
        candidate: InterviewCandidate,
        *,
        confirmed_at=None,
    ):
        cls.ensure_confirm_hire_eligible(candidate)
        now = confirmed_at or timezone.now()
        candidate.is_hired = True
        candidate.hired_at = now
        candidate.offer_status = InterviewCandidate.OFFER_STATUS_CONFIRMED

    @classmethod
    def ensure_status_change_allowed(
        cls,
        candidate: InterviewCandidate,
        next_status: str,
    ) -> str:
        before_status = cls.resolve_offer_status(candidate)
        if (
            before_status == InterviewCandidate.OFFER_STATUS_CONFIRMED
            and next_status != before_status
        ):
            raise OfferStatusTransitionError(
                code="confirmed_status_locked",
                error="已确认入职为最终状态，不可修改",
                details={"offer_status": ["当前候选人已确认入职，状态不可再修改"]},
            )
        return before_status

    @classmethod
    def apply_offer_status_change(
        cls,
        candidate: InterviewCandidate,
        next_status: str,
    ) -> tuple[str, bool]:
        before_status = cls.ensure_status_change_allowed(candidate, next_status)
        if next_status == before_status:
            return before_status, False

        candidate.offer_status = next_status
        if next_status == InterviewCandidate.OFFER_STATUS_CONFIRMED:
            candidate.is_hired = True
            if not candidate.hired_at:
                candidate.hired_at = timezone.now()
        else:
            candidate.is_hired = False
            candidate.hired_at = None

        return before_status, True
