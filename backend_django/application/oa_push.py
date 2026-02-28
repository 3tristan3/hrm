"""OA 推送服务：负责 token 获取、字段映射、流程创建与状态落库。"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import InterviewCandidate

logger = logging.getLogger(__name__)


# 统一错误码：用于前端展示、日志检索和重试策略判断。
OA_PUSH_ERROR_DISABLED = "OA_DISABLED"
OA_PUSH_ERROR_CONFIG = "OA_CONFIG_ERROR"
OA_PUSH_ERROR_PAYLOAD = "OA_PAYLOAD_INVALID"
OA_PUSH_ERROR_TOKEN_EXPIRED = "OA_TOKEN_EXPIRED"
OA_PUSH_ERROR_AUTH = "OA_AUTH_ERROR"
OA_PUSH_ERROR_PERMISSION = "OA_PERMISSION_ERROR"
OA_PUSH_ERROR_PARAM = "OA_PARAM_ERROR"
OA_PUSH_ERROR_SERVER = "OA_SERVER_ERROR"
OA_PUSH_ERROR_NETWORK = "OA_NETWORK_ERROR"
OA_PUSH_ERROR_RUNTIME = "OA_RUNTIME_ERROR"


@dataclass
class OAPushResult:
    success: bool
    retryable: bool
    error_code: str = ""
    error_message: str = ""
    oa_code: str = ""
    oa_message: str = ""
    request_id: str = ""
    payload_snapshot: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "success": bool(self.success),
            "retryable": bool(self.retryable),
            "error_code": self.error_code or "",
            "error_message": self.error_message or "",
            "oa_code": self.oa_code or "",
            "oa_message": self.oa_message or "",
            "request_id": self.request_id or "",
        }


class _SafeFormatDict(dict):
    """模板渲染缺失键时返回空串，避免 format 抛 KeyError。"""

    def __missing__(self, key):
        return ""


_TOKEN_CACHE: dict[str, Any] = {
    "token": "",
    "expires_at": None,
}


def _is_enabled() -> bool:
    return bool(getattr(settings, "OA_PUSH_ENABLED", False))


def _now() -> datetime:
    return timezone.now()


def _get_timeout_seconds() -> int:
    return max(int(getattr(settings, "OA_PUSH_REQUEST_TIMEOUT_SECONDS", 10) or 10), 1)


def _token_ttl_seconds() -> int:
    return max(int(getattr(settings, "OA_PUSH_TOKEN_TTL_SECONDS", 1800) or 1800), 60)


def _auto_retry_times() -> int:
    return max(int(getattr(settings, "OA_PUSH_AUTO_RETRY_TIMES", 1) or 1), 0)


def _content_type() -> str:
    value = str(
        getattr(
            settings,
            "OA_PUSH_CONTENT_TYPE",
            "application/x-www-form-urlencoded; charset=utf-8",
        )
        or "application/x-www-form-urlencoded; charset=utf-8"
    ).strip()
    return value or "application/x-www-form-urlencoded; charset=utf-8"


def _oa_base_url() -> str:
    return str(getattr(settings, "OA_PUSH_BASE_URL", "") or "").strip().rstrip("/")


def _required_config() -> dict[str, str]:
    return {
        "OA_PUSH_BASE_URL": _oa_base_url(),
        "OA_PUSH_APP_ID": str(getattr(settings, "OA_PUSH_APP_ID", "") or "").strip(),
        "OA_PUSH_SECRIT": str(getattr(settings, "OA_PUSH_SECRIT", "") or "").strip(),
        "OA_PUSH_SPK": str(getattr(settings, "OA_PUSH_SPK", "") or "").strip(),
        "OA_PUSH_USER_ID": str(getattr(settings, "OA_PUSH_USER_ID", "") or "").strip(),
        "OA_PUSH_WORKFLOW_ID": str(getattr(settings, "OA_PUSH_WORKFLOW_ID", "") or "").strip(),
    }


def _missing_required_keys() -> list[str]:
    required = _required_config()
    return [name for name, value in required.items() if not value]


def _normalize_public_key(spk: str) -> str:
    """兼容仅提供裸 Base64 的公钥，自动封装为 PEM。"""
    key = str(spk or "").strip()
    if "BEGIN PUBLIC KEY" in key or "BEGIN RSA PUBLIC KEY" in key:
        return key
    compact = "".join(key.split())
    lines = [compact[i : i + 64] for i in range(0, len(compact), 64)]
    body = "\n".join(lines)
    return f"-----BEGIN PUBLIC KEY-----\n{body}\n-----END PUBLIC KEY-----"


def _encrypt_text_with_spk(spk: str, plain_text: str) -> str:
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except Exception as err:
        raise RuntimeError("缺少 cryptography 依赖，无法执行 OA 加密") from err

    pem = _normalize_public_key(spk).encode("utf-8")
    public_key = serialization.load_pem_public_key(pem)
    encrypted = public_key.encrypt(
        str(plain_text or "").encode("utf-8"),
        padding.PKCS1v15(),
    )
    return base64.b64encode(encrypted).decode("utf-8")


def _resolve_source(candidate: InterviewCandidate, source: str, default: Any = "") -> Any:
    """按 source 路径取值，支持 application./candidate./constant. 前缀。"""
    path = str(source or "").strip()
    if not path:
        return default

    if path.startswith("constant."):
        return path[len("constant.") :]

    target: Any = candidate
    if path.startswith("application."):
        target = candidate.application
        path = path[len("application.") :]
    elif path.startswith("candidate."):
        target = candidate
        path = path[len("candidate.") :]

    current = target
    for part in path.split("."):
        if not part:
            continue
        if isinstance(current, dict):
            current = current.get(part, default)
        else:
            current = getattr(current, part, default)
        if current is default:
            return default
    return current


def _normalize_field_value(value: Any, *, raw: bool) -> Any:
    if value is None:
        return ""
    if raw:
        return value
    if isinstance(value, datetime):
        return timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _build_main_data(candidate: InterviewCandidate) -> list[dict[str, Any]]:
    # 主表字段完全由配置驱动，避免字段变更时改代码。
    mappings = getattr(settings, "OA_PUSH_MAIN_FIELD_MAPPINGS", [])
    if not isinstance(mappings, list):
        raise RuntimeError("OA_PUSH_MAIN_FIELD_MAPPINGS 必须是数组")
    if not mappings:
        raise RuntimeError("OA_PUSH_MAIN_FIELD_MAPPINGS 为空，无法构建主表字段")

    rows: list[dict[str, Any]] = []
    for raw_mapping in mappings:
        if not isinstance(raw_mapping, dict):
            raise RuntimeError("OA_PUSH_MAIN_FIELD_MAPPINGS 包含非法项")
        oa_field = str(raw_mapping.get("oa_field") or "").strip()
        source = str(raw_mapping.get("source") or "").strip()
        if not oa_field:
            raise RuntimeError("OA_PUSH_MAIN_FIELD_MAPPINGS 存在空 oa_field")
        default = raw_mapping.get("default", "")
        raw = bool(raw_mapping.get("raw", False))
        value = _resolve_source(candidate, source, default=default)
        if value in (None, "") and "default" in raw_mapping:
            value = default
        rows.append(
            {
                "fieldName": oa_field,
                "fieldValue": _normalize_field_value(value, raw=raw),
            }
        )
    return rows


def _build_request_name(candidate: InterviewCandidate) -> str:
    template = str(
        getattr(settings, "OA_PUSH_REQUEST_NAME_TEMPLATE", "入职确认-{name}") or "入职确认-{name}"
    )
    context = _SafeFormatDict(
        {
            "name": str(candidate.application.name or ""),
            "phone": str(candidate.application.phone or ""),
            "job": str(getattr(candidate.application.job, "title", "") or ""),
            "candidate_id": str(candidate.id),
            "application_id": str(candidate.application_id),
        }
    )
    return template.format_map(context).strip() or f"入职确认-{candidate.application.name}"


def _build_request_payload(candidate: InterviewCandidate) -> dict[str, Any]:
    """组装 doCreateRequest 请求体。"""
    detail_data = getattr(settings, "OA_PUSH_DETAIL_DATA_TEMPLATE", [])
    other_params = getattr(settings, "OA_PUSH_OTHER_PARAMS", {})
    if not isinstance(detail_data, list):
        detail_data = []
    if not isinstance(other_params, dict):
        other_params = {}

    request_level = str(getattr(settings, "OA_PUSH_REQUEST_LEVEL", "") or "").strip()
    remark_template = str(getattr(settings, "OA_PUSH_REMARK_TEMPLATE", "") or "")
    remark = remark_template.format_map(
        _SafeFormatDict(
            {
                "name": str(candidate.application.name or ""),
                "phone": str(candidate.application.phone or ""),
                "candidate_id": str(candidate.id),
                "application_id": str(candidate.application_id),
            }
        )
    )

    payload: dict[str, Any] = {
        "workflowId": str(getattr(settings, "OA_PUSH_WORKFLOW_ID", "") or "").strip(),
        "requestName": _build_request_name(candidate),
        "mainData": _build_main_data(candidate),
        "detailData": detail_data,
        "otherParams": other_params,
        "requestLevel": request_level,
        "remark": remark,
    }
    return payload


def _extract_token(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    token = payload.get("token")
    if token:
        return str(token)
    data = payload.get("data")
    if isinstance(data, dict) and data.get("token"):
        return str(data.get("token"))
    return ""


def _is_token_invalid(message: str, code: str = "") -> bool:
    text = f"{code} {message}".lower()
    return ("token" in text and ("超时" in text or "不存在" in text or "invalid" in text)) or "token expired" in text


def _extract_request_id(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    data = payload.get("data")
    if isinstance(data, dict):
        if data.get("requestid") is not None:
            return str(data.get("requestid"))
        if data.get("requestId") is not None:
            return str(data.get("requestId"))
    if payload.get("requestid") is not None:
        return str(payload.get("requestid"))
    if payload.get("requestId") is not None:
        return str(payload.get("requestId"))
    return ""


def _build_push_headers(*, token: str, encrypted_userid: str) -> dict[str, str]:
    return {
        "appid": str(getattr(settings, "OA_PUSH_APP_ID", "") or "").strip(),
        "token": token,
        "userid": encrypted_userid,
        "Content-Type": _content_type(),
    }


def _request_json(response: requests.Response) -> dict[str, Any]:
    try:
        return response.json()
    except ValueError:
        return {}


def _classify_oa_failure(payload: dict[str, Any], *, http_status: int = 200) -> OAPushResult:
    """把 OA 返回统一映射为内部失败类型，驱动后续自动重试。"""
    code = str(payload.get("code") or "").strip()
    err_msg_raw = payload.get("errMsg", "")
    if isinstance(err_msg_raw, dict):
        err_msg = json.dumps(err_msg_raw, ensure_ascii=False)
    else:
        err_msg = str(err_msg_raw or payload.get("message") or payload.get("msg") or "")
    request_id = _extract_request_id(payload)

    if request_id:
        return OAPushResult(
            success=True,
            retryable=False,
            request_id=request_id,
            oa_code=code,
            oa_message=err_msg,
        )

    if _is_token_invalid(err_msg, code):
        return OAPushResult(
            success=False,
            retryable=True,
            error_code=OA_PUSH_ERROR_TOKEN_EXPIRED,
            error_message=err_msg or "OA token 已失效",
            oa_code=code,
            oa_message=err_msg,
        )
    upper_code = code.upper()
    if upper_code == "NO_PERMISSION":
        return OAPushResult(
            success=False,
            retryable=False,
            error_code=OA_PUSH_ERROR_PERMISSION,
            error_message=err_msg or "OA 权限不足",
            oa_code=code,
            oa_message=err_msg,
        )
    if upper_code == "PARAM_ERROR":
        return OAPushResult(
            success=False,
            retryable=False,
            error_code=OA_PUSH_ERROR_PARAM,
            error_message=err_msg or "OA 参数错误",
            oa_code=code,
            oa_message=err_msg,
        )
    if http_status >= 500 or upper_code in {"SYSTEM_INNER_ERROR", "USER_EXCEPTION"}:
        return OAPushResult(
            success=False,
            retryable=True,
            error_code=OA_PUSH_ERROR_SERVER,
            error_message=err_msg or "OA 服务异常",
            oa_code=code,
            oa_message=err_msg,
        )
    if http_status >= 400:
        return OAPushResult(
            success=False,
            retryable=False,
            error_code=OA_PUSH_ERROR_AUTH,
            error_message=err_msg or f"OA 请求失败({http_status})",
            oa_code=code,
            oa_message=err_msg,
        )
    return OAPushResult(
        success=False,
        retryable=False,
        error_code=OA_PUSH_ERROR_RUNTIME,
        error_message=err_msg or "OA 返回异常",
        oa_code=code,
        oa_message=err_msg,
    )


def _cached_token_available() -> bool:
    # 提前 60 秒视为过期，规避边界时间抖动。
    token = str(_TOKEN_CACHE.get("token") or "")
    expires_at = _TOKEN_CACHE.get("expires_at")
    if not token or not expires_at:
        return False
    if not isinstance(expires_at, datetime):
        return False
    return expires_at > (_now() + timedelta(seconds=60))


def _fetch_token(force_refresh: bool = False) -> OAPushResult:
    """获取 token：优先读缓存，失效后走 applytoken。"""
    if not force_refresh and _cached_token_available():
        return OAPushResult(
            success=True,
            retryable=False,
            request_id=str(_TOKEN_CACHE.get("token") or ""),
        )

    base_url = _oa_base_url()
    endpoint = f"{base_url}/api/ec/dev/auth/applytoken"
    config = _required_config()

    encrypted_secret = _encrypt_text_with_spk(config["OA_PUSH_SPK"], config["OA_PUSH_SECRIT"])
    headers = {
        "appid": config["OA_PUSH_APP_ID"],
        "secret": encrypted_secret,
        "time": str(_token_ttl_seconds()),
        "Content-Type": _content_type(),
    }

    try:
        response = requests.post(endpoint, headers=headers, timeout=_get_timeout_seconds())
    except requests.RequestException as err:
        return OAPushResult(
            success=False,
            retryable=True,
            error_code=OA_PUSH_ERROR_NETWORK,
            error_message=f"OA 获取 token 网络异常：{err}",
        )

    payload = _request_json(response)
    token = _extract_token(payload)
    if response.status_code >= 400:
        result = _classify_oa_failure(payload, http_status=response.status_code)
        if not result.error_code:
            result.error_code = OA_PUSH_ERROR_AUTH
            result.error_message = result.error_message or "OA 获取 token 失败"
        return result
    if not token:
        result = _classify_oa_failure(payload, http_status=response.status_code)
        if not result.error_code:
            result.error_code = OA_PUSH_ERROR_RUNTIME
            result.error_message = result.error_message or "OA 返回 token 为空"
        return result

    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expires_at"] = _now() + timedelta(seconds=_token_ttl_seconds())
    return OAPushResult(success=True, retryable=False, request_id=token)


def _build_form_payload(payload: dict[str, Any]) -> dict[str, str]:
    """OA 表单模式下，复杂字段需序列化为 JSON 字符串。"""
    form_payload: dict[str, str] = {
        "workflowId": str(payload.get("workflowId") or ""),
        "requestName": str(payload.get("requestName") or ""),
        "mainData": json.dumps(payload.get("mainData") or [], ensure_ascii=False),
    }
    if payload.get("detailData") is not None:
        form_payload["detailData"] = json.dumps(payload.get("detailData") or [], ensure_ascii=False)
    if payload.get("otherParams") is not None:
        form_payload["otherParams"] = json.dumps(payload.get("otherParams") or {}, ensure_ascii=False)
    if payload.get("requestLevel") not in (None, ""):
        form_payload["requestLevel"] = str(payload.get("requestLevel"))
    if payload.get("remark") not in (None, ""):
        form_payload["remark"] = str(payload.get("remark"))
    return form_payload


def _create_request_with_token(
    *,
    token: str,
    encrypted_userid: str,
    payload: dict[str, Any],
) -> OAPushResult:
    """使用已有 token 调用 doCreateRequest。"""
    base_url = _oa_base_url()
    endpoint = f"{base_url}/api/workflow/paService/doCreateRequest"
    headers = _build_push_headers(token=token, encrypted_userid=encrypted_userid)
    timeout = _get_timeout_seconds()

    content_type = _content_type().lower()
    data: Any = None
    json_payload: dict[str, Any] | None = None
    if "application/json" in content_type:
        json_payload = payload
    else:
        data = _build_form_payload(payload)

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            data=data,
            json=json_payload,
            timeout=timeout,
        )
    except requests.RequestException as err:
        return OAPushResult(
            success=False,
            retryable=True,
            error_code=OA_PUSH_ERROR_NETWORK,
            error_message=f"OA 推送网络异常：{err}",
        )

    response_payload = _request_json(response)
    result = _classify_oa_failure(response_payload, http_status=response.status_code)
    result.payload_snapshot = payload
    if result.success:
        result.error_code = ""
        result.error_message = ""
    return result


def _push_once(candidate: InterviewCandidate) -> OAPushResult:
    """一次完整推送：构建 payload -> 取 token -> 创建流程。"""
    missing_keys = _missing_required_keys()
    if missing_keys:
        return OAPushResult(
            success=False,
            retryable=False,
            error_code=OA_PUSH_ERROR_CONFIG,
            error_message=f"OA 配置缺失：{','.join(missing_keys)}",
        )

    try:
        payload = _build_request_payload(candidate)
    except Exception as err:
        return OAPushResult(
            success=False,
            retryable=False,
            error_code=OA_PUSH_ERROR_PAYLOAD,
            error_message=f"OA 请求体构建失败：{err}",
        )

    token_result = _fetch_token(force_refresh=False)
    if not token_result.success:
        token_result.payload_snapshot = payload
        return token_result

    token = str(_TOKEN_CACHE.get("token") or "")
    config = _required_config()
    encrypted_userid = _encrypt_text_with_spk(config["OA_PUSH_SPK"], config["OA_PUSH_USER_ID"])
    result = _create_request_with_token(token=token, encrypted_userid=encrypted_userid, payload=payload)
    if result.success:
        return result
    if result.error_code == OA_PUSH_ERROR_TOKEN_EXPIRED:
        # token 失效时强制刷新后再试一次，避免把瞬时过期直接判失败。
        refresh_result = _fetch_token(force_refresh=True)
        if not refresh_result.success:
            refresh_result.payload_snapshot = payload
            return refresh_result
        refreshed_token = str(_TOKEN_CACHE.get("token") or "")
        retry_result = _create_request_with_token(
            token=refreshed_token,
            encrypted_userid=encrypted_userid,
            payload=payload,
        )
        if retry_result.success:
            return retry_result
        return retry_result
    return result


def _mark_pending(candidate: InterviewCandidate, *, is_retry: bool) -> None:
    """发起推送前先落库 pending，保证链路可追踪。"""
    now = _now()
    current_retry = int(candidate.oa_push_retry_count or 0)
    candidate.oa_push_retry_count = current_retry + 1
    candidate.oa_push_status = InterviewCandidate.OA_PUSH_STATUS_PENDING
    candidate.oa_push_last_attempt_at = now
    candidate.oa_push_error_code = ""
    candidate.oa_push_error_message = ""
    candidate.oa_push_oa_code = ""
    candidate.oa_push_oa_message = ""
    candidate.save(
        update_fields=[
            "oa_push_retry_count",
            "oa_push_status",
            "oa_push_last_attempt_at",
            "oa_push_error_code",
            "oa_push_error_message",
            "oa_push_oa_code",
            "oa_push_oa_message",
            "updated_at",
        ]
    )
    if is_retry:
        logger.info("oa_push_retry candidate_id=%s retry_count=%s", candidate.id, candidate.oa_push_retry_count)


def _mark_result(candidate: InterviewCandidate, result: OAPushResult) -> None:
    """推送结束后统一回写状态、失败原因、OA 返回码和请求快照。"""
    now = _now()
    candidate.oa_push_payload_snapshot = result.payload_snapshot or {}
    if result.success:
        candidate.oa_push_status = InterviewCandidate.OA_PUSH_STATUS_SUCCESS
        candidate.oa_push_success_at = now
        candidate.oa_push_request_id = str(result.request_id or "")
        candidate.oa_push_error_code = ""
        candidate.oa_push_error_message = ""
        candidate.oa_push_oa_code = str(result.oa_code or "")
        candidate.oa_push_oa_message = str(result.oa_message or "")
    else:
        candidate.oa_push_status = InterviewCandidate.OA_PUSH_STATUS_FAILED
        candidate.oa_push_request_id = ""
        candidate.oa_push_error_code = str(result.error_code or OA_PUSH_ERROR_RUNTIME)
        candidate.oa_push_error_message = str(result.error_message or "OA 推送失败")
        candidate.oa_push_oa_code = str(result.oa_code or "")
        candidate.oa_push_oa_message = str(result.oa_message or "")
    candidate.save(
        update_fields=[
            "oa_push_status",
            "oa_push_success_at",
            "oa_push_request_id",
            "oa_push_error_code",
            "oa_push_error_message",
            "oa_push_oa_code",
            "oa_push_oa_message",
            "oa_push_payload_snapshot",
            "updated_at",
        ]
    )


def dispatch_oa_push(candidate_id: int, *, is_retry: bool = False) -> tuple[InterviewCandidate, OAPushResult]:
    """对外入口：幂等保护 + 自动重试 + 状态落库。"""
    with transaction.atomic():
        candidate = (
            InterviewCandidate.objects.select_for_update()
            .select_related("application", "application__job", "application__region")
            .get(pk=candidate_id)
        )
        if candidate.oa_push_status == InterviewCandidate.OA_PUSH_STATUS_SUCCESS and candidate.oa_push_request_id:
            # 已成功且存在 request_id 时直接幂等返回，避免重复建 OA 流程。
            return candidate, OAPushResult(
                success=True,
                retryable=False,
                request_id=candidate.oa_push_request_id,
                oa_message="已推送成功，跳过重复创建",
                payload_snapshot=candidate.oa_push_payload_snapshot or {},
            )
        _mark_pending(candidate, is_retry=is_retry)

    if not _is_enabled():
        result = OAPushResult(
            success=False,
            retryable=False,
            error_code=OA_PUSH_ERROR_DISABLED,
            error_message="OA 推送未启用",
            payload_snapshot={},
        )
    else:
        attempts = 0
        result = OAPushResult(
            success=False,
            retryable=False,
            error_code=OA_PUSH_ERROR_RUNTIME,
            error_message="OA 推送失败",
        )
        max_attempts = max(_auto_retry_times(), 0) + 1
        while attempts < max_attempts:
            # 仅对 retryable 错误继续重试。
            attempts += 1
            try:
                result = _push_once(candidate)
            except Exception as err:
                result = OAPushResult(
                    success=False,
                    retryable=True,
                    error_code=OA_PUSH_ERROR_RUNTIME,
                    error_message=f"OA 推送运行异常：{err}",
                )
            if result.success:
                break
            if not result.retryable:
                break

    with transaction.atomic():
        candidate = (
            InterviewCandidate.objects.select_for_update()
            .select_related("application", "application__job", "application__region")
            .get(pk=candidate_id)
        )
        _mark_result(candidate, result)
    return candidate, result
