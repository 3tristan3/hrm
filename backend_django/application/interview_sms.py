"""面试短信服务：负责模板参数组装、供应商发送和状态落库。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .interview_flow import InterviewFlowError
from .models import InterviewCandidate


@dataclass
class SmsDispatchResult:
    success: bool
    provider_code: str = ""
    provider_message: str = ""
    request_id: str = ""
    biz_id: str = ""
    raw: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "success": bool(self.success),
            "provider_code": self.provider_code or "",
            "provider_message": self.provider_message or "",
            "request_id": self.request_id or "",
            "biz_id": self.biz_id or "",
        }


def _is_sms_enabled() -> bool:
    return bool(getattr(settings, "INTERVIEW_SMS_ENABLED", False))


def _sms_provider() -> str:
    return str(getattr(settings, "INTERVIEW_SMS_PROVIDER", "aliyun") or "aliyun").strip().lower()


def _format_interview_time(value) -> str:
    if not value:
        return ""
    localized = timezone.localtime(value, timezone.get_current_timezone())
    return localized.strftime("%Y-%m-%d %H:%M")


def _build_interview_template_params(candidate: InterviewCandidate) -> dict[str, str]:
    application = candidate.application
    return {
        "name": str(application.name or ""),
        "job": str(getattr(application.job, "title", "") or ""),
        "round": str(max(int(candidate.interview_round or 1), 1)),
        "time": _format_interview_time(candidate.interview_at),
        "location": str(candidate.interview_location or ""),
        "interviewer": str(candidate.interviewer or ""),
        "note": str(candidate.note or ""),
    }


def _send_via_aliyun(phone: str, template_params: dict[str, str], *, out_id: str = "") -> SmsDispatchResult:
    access_key_id = str(getattr(settings, "ALIYUN_SMS_ACCESS_KEY_ID", "") or "").strip()
    access_key_secret = str(getattr(settings, "ALIYUN_SMS_ACCESS_KEY_SECRET", "") or "").strip()
    sign_name = str(getattr(settings, "ALIYUN_SMS_SIGN_NAME", "") or "").strip()
    template_code = str(getattr(settings, "ALIYUN_SMS_TEMPLATE_CODE", "") or "").strip()
    region_id = str(getattr(settings, "ALIYUN_SMS_REGION_ID", "cn-hangzhou") or "cn-hangzhou").strip()

    if not all([access_key_id, access_key_secret, sign_name, template_code]):
        return SmsDispatchResult(
            success=False,
            provider_code="SMS_CONFIG_MISSING",
            provider_message="短信配置缺失，请检查阿里云 AccessKey/签名/模板配置",
        )

    try:
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
        from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
    except Exception:
        return SmsDispatchResult(
            success=False,
            provider_code="SMS_SDK_MISSING",
            provider_message="短信 SDK 未安装，请安装 aliyun-python-sdk-core 与 aliyun-python-sdk-dysmsapi",
        )

    request = SendSmsRequest.SendSmsRequest()
    request.set_accept_format("json")
    request.set_PhoneNumbers(phone)
    request.set_SignName(sign_name)
    request.set_TemplateCode(template_code)
    request.set_TemplateParam(json.dumps(template_params, ensure_ascii=False))
    if out_id:
        request.set_OutId(out_id)

    client = AcsClient(access_key_id, access_key_secret, region_id)
    try:
        raw_bytes = client.do_action_with_exception(request)
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (ClientException, ServerException) as err:
        return SmsDispatchResult(
            success=False,
            provider_code=getattr(err, "error_code", "") or "SMS_REQUEST_ERROR",
            provider_message=str(err),
        )
    except Exception as err:
        return SmsDispatchResult(
            success=False,
            provider_code="SMS_REQUEST_ERROR",
            provider_message=str(err),
        )

    code = str(payload.get("Code", "") or "")
    message = str(payload.get("Message", "") or "")
    return SmsDispatchResult(
        success=(code == "OK"),
        provider_code=code,
        provider_message=message,
        request_id=str(payload.get("RequestId", "") or ""),
        biz_id=str(payload.get("BizId", "") or ""),
        raw=payload,
    )


def _send_interview_sms(candidate: InterviewCandidate) -> SmsDispatchResult:
    if not _is_sms_enabled():
        return SmsDispatchResult(
            success=False,
            provider_code="SMS_DISABLED",
            provider_message="短信功能未启用",
        )

    phone = str(candidate.application.phone or "").strip()
    if not phone:
        return SmsDispatchResult(
            success=False,
            provider_code="SMS_PHONE_EMPTY",
            provider_message="候选人手机号为空，无法发送短信",
        )

    provider = _sms_provider()
    params = _build_interview_template_params(candidate)
    if provider == "aliyun":
        return _send_via_aliyun(phone, params, out_id=str(candidate.id))

    return SmsDispatchResult(
        success=False,
        provider_code="SMS_PROVIDER_UNSUPPORTED",
        provider_message=f"不支持的短信供应商：{provider}",
    )


def _validate_sms_send_precondition(candidate: InterviewCandidate) -> None:
    if candidate.status != InterviewCandidate.STATUS_SCHEDULED or not candidate.interview_at:
        raise InterviewFlowError(
            code="INTERVIEW_NOT_SCHEDULED",
            message="当前未安排面试",
        )


def _mark_sms_sending(candidate: InterviewCandidate, *, is_retry: bool) -> None:
    now = timezone.now()
    current_retry = int(candidate.sms_retry_count or 0)
    candidate.sms_retry_count = current_retry + 1 if is_retry else 0
    candidate.sms_status = InterviewCandidate.SMS_STATUS_SENDING
    candidate.sms_error = ""
    candidate.sms_last_attempt_at = now
    candidate.sms_updated_at = now
    candidate.sms_provider_code = ""
    candidate.sms_provider_message = ""
    candidate.sms_message_id = ""
    candidate.sms_sent_at = None
    candidate.save(
        update_fields=[
            "sms_retry_count",
            "sms_status",
            "sms_error",
            "sms_last_attempt_at",
            "sms_updated_at",
            "sms_provider_code",
            "sms_provider_message",
            "sms_message_id",
            "sms_sent_at",
            "updated_at",
        ]
    )


def _mark_sms_result(candidate: InterviewCandidate, result: SmsDispatchResult) -> None:
    now = timezone.now()
    candidate.sms_status = (
        InterviewCandidate.SMS_STATUS_SUCCESS
        if result.success
        else InterviewCandidate.SMS_STATUS_FAILED
    )
    candidate.sms_updated_at = now
    candidate.sms_provider_code = str(result.provider_code or "")
    candidate.sms_provider_message = str(result.provider_message or "")
    candidate.sms_message_id = str(result.biz_id or "")
    candidate.sms_error = "" if result.success else str(result.provider_message or "短信发送失败")
    if result.success:
        candidate.sms_sent_at = now
    candidate.save(
        update_fields=[
            "sms_status",
            "sms_updated_at",
            "sms_provider_code",
            "sms_provider_message",
            "sms_message_id",
            "sms_error",
            "sms_sent_at",
            "updated_at",
        ]
    )


def dispatch_interview_schedule_sms(
    candidate_id: int, *, is_retry: bool = False
) -> tuple[InterviewCandidate, SmsDispatchResult]:
    """发送面试安排短信并更新候选人短信状态。"""
    with transaction.atomic():
        candidate = (
            InterviewCandidate.objects.select_for_update()
            .select_related("application", "application__job")
            .get(pk=candidate_id)
        )
        _validate_sms_send_precondition(candidate)
        _mark_sms_sending(candidate, is_retry=is_retry)

    try:
        result = _send_interview_sms(candidate)
    except Exception as err:
        result = SmsDispatchResult(
            success=False,
            provider_code="SMS_RUNTIME_ERROR",
            provider_message=str(err),
        )

    with transaction.atomic():
        candidate = (
            InterviewCandidate.objects.select_for_update()
            .select_related("application", "application__job")
            .get(pk=candidate_id)
        )
        _mark_sms_result(candidate, result)
    return candidate, result
