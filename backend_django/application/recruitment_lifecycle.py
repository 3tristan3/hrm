"""招聘流程内部结算状态：用于岗位删除准入判断。"""

from .models import InterviewCandidate


OUTCOME_PENDING = "pending"
OUTCOME_PASSED = "passed"
OUTCOME_TALENT = "talent"
OUTCOME_HIRED = "hired"


def resolve_candidate_outcome(candidate: InterviewCandidate) -> str:
    """将现有面试字段映射为内部结算状态。"""
    if candidate.status in (
        InterviewCandidate.STATUS_PENDING,
        InterviewCandidate.STATUS_SCHEDULED,
    ):
        return OUTCOME_PENDING

    if candidate.status == InterviewCandidate.STATUS_COMPLETED:
        if candidate.result == InterviewCandidate.RESULT_REJECT:
            return OUTCOME_TALENT
        if candidate.result == InterviewCandidate.RESULT_PASS:
            if bool(getattr(candidate, "is_hired", False)):
                return OUTCOME_HIRED
            return OUTCOME_PASSED

    return OUTCOME_PENDING


def summarize_interview_outcomes(candidates) -> dict:
    summary = {
        OUTCOME_PENDING: 0,
        OUTCOME_PASSED: 0,
        OUTCOME_TALENT: 0,
        OUTCOME_HIRED: 0,
        "total": 0,
    }
    for item in candidates:
        outcome = resolve_candidate_outcome(item)
        summary[outcome] += 1
        summary["total"] += 1
    return summary
