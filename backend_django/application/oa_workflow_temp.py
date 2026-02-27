"""临时 OA 流程推送客户端：用于确认入职后最小字段推送（姓名+手机号）。"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


@dataclass
class OATempPushResult:
    enabled: bool
    success: bool
    code: str = ""
    error: str = ""
    request_id: str = ""
    raw: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.enabled),
            "success": bool(self.success),
            "code": self.code or "",
            "error": self.error or "",
            "request_id": self.request_id or "",
        }


def _load_public_key(public_key_text: str):
    try:
        from cryptography.hazmat.primitives import serialization
    except Exception as err:
        raise RuntimeError("缺少 cryptography 依赖，无法执行 OA 加密") from err

    text = str(public_key_text or "").strip()
    if not text:
        raise ValueError("SPK 为空")
    if "BEGIN PUBLIC KEY" in text:
        return serialization.load_pem_public_key(text.encode("utf-8"))
    raw = base64.b64decode(text)
    return serialization.load_der_public_key(raw)


def _encrypt_text_with_spk(plain_text: str, spk: str) -> str:
    try:
        from cryptography.hazmat.primitives.asymmetric import padding
    except Exception as err:
        raise RuntimeError("缺少 cryptography 依赖，无法执行 OA 加密") from err

    public_key = _load_public_key(spk)
    encrypted = public_key.encrypt(
        str(plain_text or "").encode("utf-8"),
        padding.PKCS1v15(),
    )
    return base64.b64encode(encrypted).decode("utf-8")


def _extract_request_id(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("requestid", "requestId", "requestID"):
            if key in payload and payload[key] not in (None, ""):
                return str(payload[key])
        for nested in ("data", "result"):
            if nested in payload:
                nested_id = _extract_request_id(payload[nested])
                if nested_id:
                    return nested_id
    if isinstance(payload, list):
        for item in payload:
            nested_id = _extract_request_id(item)
            if nested_id:
                return nested_id
    return ""


class OAWorkflowTempClient:
    """临时 OA 客户端：每次调用时申请 token 后创建流程。"""

    def __init__(self):
        self.enabled = bool(getattr(settings, "OA_ENABLED", False))
        self.base_url = str(getattr(settings, "OA_BASE_URL", "") or "").strip().rstrip("/")
        self.app_id = str(getattr(settings, "OA_APP_ID", "") or "").strip()
        self.secrit = str(getattr(settings, "OA_SECRIT", "") or "").strip()
        self.spk = str(getattr(settings, "OA_SPK", "") or "").strip()
        self.user_id = str(getattr(settings, "OA_USER_ID", "") or "").strip()
        self.workflow_id = str(getattr(settings, "OA_WORKFLOW_ID", "") or "").strip()
        self.timeout = max(int(getattr(settings, "OA_REQUEST_TIMEOUT_SECONDS", 10) or 10), 1)
        self.token_ttl = max(int(getattr(settings, "OA_TOKEN_TTL_SECONDS", 1800) or 1800), 60)
        self.request_name_template = str(
            getattr(settings, "OA_REQUEST_NAME_TEMPLATE", "入职确认-{name}") or "入职确认-{name}"
        )
        self.name_field = str(getattr(settings, "OA_HIRE_NAME_FIELD", "xm") or "xm").strip()
        self.phone_field = str(getattr(settings, "OA_HIRE_PHONE_FIELD", "sjh") or "sjh").strip()

    def _check_config(self) -> str:
        if not self.enabled:
            return ""
        required = {
            "OA_BASE_URL": self.base_url,
            "OA_APP_ID": self.app_id,
            "OA_SECRIT": self.secrit,
            "OA_SPK": self.spk,
            "OA_USER_ID": self.user_id,
            "OA_WORKFLOW_ID": self.workflow_id,
            "OA_HIRE_NAME_FIELD": self.name_field,
            "OA_HIRE_PHONE_FIELD": self.phone_field,
        }
        missing = [key for key, value in required.items() if not value]
        return f"配置缺失: {', '.join(missing)}" if missing else ""

    def _apply_token(self) -> str:
        encrypt_secret = _encrypt_text_with_spk(self.secrit, self.spk)
        headers = {
            "appid": self.app_id,
            "secret": encrypt_secret,
            "time": str(self.token_ttl),
        }
        url = f"{self.base_url}/api/ec/dev/auth/applytoken"
        response = requests.post(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if not bool(payload.get("status")):
            raise RuntimeError(payload.get("msg") or "OA 获取 token 失败")
        token = str(payload.get("token") or "").strip()
        if not token:
            raise RuntimeError("OA 返回 token 为空")
        return token

    def _create_request(self, token: str, *, name: str, phone: str) -> OATempPushResult:
        encrypt_userid = _encrypt_text_with_spk(self.user_id, self.spk)
        headers = {
            "appid": self.app_id,
            "token": token,
            "userid": encrypt_userid,
        }
        request_name = self.request_name_template.format(name=name or "", phone=phone or "")
        payload = {
            "workflowId": self.workflow_id,
            "requestName": request_name,
            "mainData": [
                {"fieldName": self.name_field, "fieldValue": str(name or "")},
                {"fieldName": self.phone_field, "fieldValue": str(phone or "")},
            ],
        }
        url = f"{self.base_url}/api/workflow/paService/doCreateRequest"
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        body = response.json()
        request_id = _extract_request_id(body)
        code = str(body.get("code") or "")
        success = bool(request_id) and code in ("SUCCESS", "0", "success")
        return OATempPushResult(
            enabled=True,
            success=success,
            code=code or "UNKNOWN",
            error="" if success else (str(body.get("errMsg") or body.get("msg") or "流程创建失败")),
            request_id=request_id,
            raw=body if isinstance(body, dict) else {},
        )

    def push_hire_basic_info(self, *, name: str, phone: str) -> OATempPushResult:
        if not self.enabled:
            return OATempPushResult(enabled=False, success=False, code="OA_DISABLED", error="OA 推送未启用")
        if not name or not phone:
            return OATempPushResult(
                enabled=True,
                success=False,
                code="OA_PAYLOAD_INVALID",
                error="姓名或手机号为空",
            )
        config_error = self._check_config()
        if config_error:
            return OATempPushResult(
                enabled=True,
                success=False,
                code="OA_CONFIG_ERROR",
                error=config_error,
            )
        try:
            token = self._apply_token()
            return self._create_request(token, name=name, phone=phone)
        except Exception as err:
            return OATempPushResult(
                enabled=True,
                success=False,
                code="OA_RUNTIME_ERROR",
                error=str(err),
            )
