"""OA 人员信息同步：在 OA 登录链路中按 loginid 同步姓名到本地账号。"""
from __future__ import annotations

import json
import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model

from .oa_push import (
    encrypt_oa_text_with_spk,
    fetch_oa_token_value,
    get_oa_auth_config,
    get_oa_request_timeout_seconds,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def _profile_sync_enabled() -> bool:
    return bool(getattr(settings, "OA_HRM_PROFILE_SYNC_ENABLED", False))


def _sync_once_enabled() -> bool:
    return bool(getattr(settings, "OA_HRM_PROFILE_SYNC_ONCE", True))


def _profile_config() -> dict[str, str]:
    config = get_oa_auth_config()
    return {
        "base_url": str(config.get("base_url") or "").strip().rstrip("/"),
        "app_id": str(config.get("app_id") or "").strip(),
        "secrit": str(config.get("secrit") or "").strip(),
        "spk": str(config.get("spk") or "").strip(),
        "user_id": str(config.get("user_id") or "").strip(),
    }


def _profile_config_ready(config: dict[str, str]) -> bool:
    return all(bool(config.get(key)) for key in ("base_url", "app_id", "secrit", "spk", "user_id"))


def _query_real_name_by_loginid(loginid: str, *, config: dict[str, str]) -> str:
    token = fetch_oa_token_value(force_refresh=False)
    if not token:
        return ""
    encrypted_userid = encrypt_oa_text_with_spk(config["user_id"], spk=config["spk"])
    if not encrypted_userid:
        return ""
    endpoint = f"{config['base_url']}/api/hrm/resful/getHrmUserInfoWithPage"
    headers = {
        "appid": config["app_id"],
        "token": token,
        "userid": encrypted_userid,
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    }
    body = {
        "params": json.dumps(
            {"loginid": loginid, "pagesize": 1, "curpage": 1},
            ensure_ascii=False,
        )
    }
    response = requests.post(
        endpoint,
        headers=headers,
        data=body,
        timeout=get_oa_request_timeout_seconds(),
    )
    if response.status_code >= 400:
        return ""
    payload = response.json() if response.content else {}
    if str(payload.get("code") or "").strip() not in {"1", "0"}:
        return ""
    data_list = ((payload.get("data") or {}).get("dataList") or [])
    if not isinstance(data_list, list) or not data_list:
        return ""
    first = data_list[0] or {}
    return str(first.get("lastname") or "").strip()


def sync_oa_user_real_name(user: User, *, loginid: str) -> bool:
    """按 loginid 从 OA 拉取姓名并写入 user.first_name。失败不抛异常。"""
    if not _profile_sync_enabled():
        return False
    if not user or not user.pk or not loginid:
        return False
    if _sync_once_enabled() and str(user.first_name or "").strip():
        return False

    config = _profile_config()
    if not _profile_config_ready(config):
        logger.warning("oa_profile_sync_config_missing user=%s", user.pk)
        return False

    try:
        real_name = _query_real_name_by_loginid(loginid, config=config)
    except Exception as err:
        logger.warning("oa_profile_sync_failed user=%s err=%s", user.pk, err)
        return False

    real_name = str(real_name or "").strip()
    if not real_name or real_name == str(user.first_name or "").strip():
        return False
    user.first_name = real_name
    user.save(update_fields=["first_name"])
    return True
