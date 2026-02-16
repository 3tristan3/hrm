"""登录安全工具：失败计数、锁定控制与用户名规范化。"""
from __future__ import annotations

import hashlib
import time

from django.conf import settings
from django.core.cache import cache


def normalize_login_username(username: str) -> str:
    """统一用户名输入格式，避免大小写/空格导致计数分散。"""
    return (username or "").strip().lower()


def _key(prefix: str, username: str) -> str:
    digest = hashlib.sha256(username.encode("utf-8")).hexdigest()
    return f"auth:{prefix}:{digest}"


def get_lock_remaining_seconds(username: str) -> int:
    """返回剩余锁定秒数，未锁定返回 0。"""
    normalized = normalize_login_username(username)
    if not normalized:
        return 0
    lock_until = cache.get(_key("lock", normalized))
    if not lock_until:
        return 0
    remaining = int(float(lock_until) - time.time())
    if remaining <= 0:
        cache.delete(_key("lock", normalized))
        return 0
    return remaining


def clear_login_failures(username: str) -> None:
    normalized = normalize_login_username(username)
    if not normalized:
        return
    cache.delete_many([_key("fail", normalized), _key("lock", normalized)])


def register_login_failure(username: str) -> tuple[bool, int]:
    """
    记录一次登录失败。

    返回:
    - is_locked: 本次是否触发锁定
    - remaining_seconds: 锁定剩余秒数（未锁定时为 0）
    """
    normalized = normalize_login_username(username)
    if not normalized:
        return False, 0

    lock_remaining = get_lock_remaining_seconds(normalized)
    if lock_remaining > 0:
        return True, lock_remaining

    max_failures = max(int(getattr(settings, "AUTH_LOGIN_MAX_FAILURES", 5)), 1)
    window_minutes = max(int(getattr(settings, "AUTH_LOGIN_FAILURE_WINDOW_MINUTES", 15)), 1)
    lock_minutes = max(int(getattr(settings, "AUTH_LOGIN_LOCK_MINUTES", 15)), 1)

    fail_key = _key("fail", normalized)
    failed_count = int(cache.get(fail_key) or 0) + 1
    cache.set(fail_key, failed_count, timeout=window_minutes * 60)

    if failed_count >= max_failures:
        cache.delete(fail_key)
        lock_seconds = lock_minutes * 60
        cache.set(_key("lock", normalized), time.time() + lock_seconds, timeout=lock_seconds)
        return True, lock_seconds

    return False, 0
