"""审计日志工具：集中封装操作日志写入逻辑。"""
from __future__ import annotations

from django.contrib.auth import get_user_model

from .models import Application, InterviewCandidate, OperationLog, Region

User = get_user_model()


def _safe_role_name(user) -> str:
    if not user:
        return ""
    if getattr(user, "is_superuser", False):
        return "superuser"
    profile = getattr(user, "profile", None)
    if profile and getattr(profile, "can_view_all", False):
        return "global_admin"
    return "regional_admin"


def _safe_region(user, explicit_region=None):
    if explicit_region is not None:
        return explicit_region
    if not user:
        return None
    profile = getattr(user, "profile", None)
    if profile and getattr(profile, "region_id", None):
        return getattr(profile, "region", None)
    return None


def request_id_from_request(request) -> str:
    if not request:
        return ""
    # 优先使用网关传递的请求ID，便于跨服务串联排查。
    return (
        getattr(request, "request_id", "")
        or
        request.headers.get("X-Request-ID")
        or request.META.get("HTTP_X_REQUEST_ID")
        or request.META.get("REQUEST_ID")
        or ""
    ).strip()


def write_operation_log(
    *,
    user: User | None,
    module: str,
    action: str,
    result: str = OperationLog.RESULT_SUCCESS,
    summary: str = "",
    details: dict | None = None,
    target_type: str = "",
    target_id: int | None = None,
    target_label: str = "",
    application: Application | None = None,
    interview_candidate: InterviewCandidate | None = None,
    region: Region | None = None,
    request_id: str = "",
) -> None:
    """写入操作日志，失败时不影响主业务流程。"""
    try:
        operator_username = getattr(user, "username", "") if user else ""
        target_region = _safe_region(user, explicit_region=region)
        OperationLog.objects.create(
            operator=user if user and getattr(user, "pk", None) else None,
            operator_username=operator_username,
            operator_role=_safe_role_name(user),
            operator_region_name=getattr(target_region, "name", "") if target_region else "",
            region=target_region,
            module=module,
            action=action,
            target_type=target_type or "",
            target_id=target_id,
            target_label=target_label or "",
            application=application,
            interview_candidate=interview_candidate,
            result=result,
            summary=summary or "",
            details=details or {},
            request_id=request_id or "",
        )
    except Exception:
        # 审计写失败不阻断业务主流程，避免影响用户操作。
        return
