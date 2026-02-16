"""共享序列化器基础能力：导入与公共函数。"""

"""DRF 序列化器定义，负责接口参数校验与响应结构组装。"""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from ..models import (
    Application,
    ApplicationAttachment,
    InterviewCandidate,
    Job,
    OperationLog,
    Region,
    RegionField,
    UserProfile,
)

User = get_user_model()


def build_public_file_url(file_field, request=None):
    if not file_field:
        return ""
    url = str(file_field.url or "")
    if not url:
        return ""
    if not url.startswith("/"):
        url = f"/{url}"
    media_base = getattr(settings, "MEDIA_BASE_URL", "")
    if media_base:
        return f"{media_base}{url}"
    return url
