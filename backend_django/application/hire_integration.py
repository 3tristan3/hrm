"""确认入职后的外部推送扩展点。"""

from .models import InterviewCandidate


def dispatch_hire_confirmation(
    candidate: InterviewCandidate,
    push_targets=None,
) -> dict:
    """预留外部平台推送能力，当前仅返回占位结果。"""
    targets = []
    for item in push_targets or []:
        value = str(item).strip()
        if value and value not in targets:
            targets.append(value)
    return {
        "enabled": False,
        "candidate_id": candidate.id,
        "targets": targets,
        "dispatched": [],
        "skipped": targets,
    }
