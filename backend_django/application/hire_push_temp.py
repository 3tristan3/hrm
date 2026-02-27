"""确认入职后临时 OA 推送封装。"""
from __future__ import annotations

from .models import InterviewCandidate
from .oa_workflow_temp import OAWorkflowTempClient


def dispatch_temp_hire_push(candidate: InterviewCandidate) -> dict:
    application = candidate.application
    name = str(application.name or "").strip()
    phone = str(application.phone or "").strip()
    result = OAWorkflowTempClient().push_hire_basic_info(name=name, phone=phone)
    return result.to_payload()
