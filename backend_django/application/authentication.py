"""认证相关扩展：为 Token 增加过期校验。"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token


class ExpiringTokenAuthentication(TokenAuthentication):
    """在 DRF TokenAuthentication 基础上增加 TTL 过期控制。"""

    model = Token

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed("无效的登录凭证")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("账号已禁用")

        ttl_hours = max(int(getattr(settings, "AUTH_TOKEN_TTL_HOURS", 24)), 0)
        if ttl_hours > 0:
            expires_at = token.created + timedelta(hours=ttl_hours)
            if timezone.now() >= expires_at:
                token.delete()
                raise exceptions.AuthenticationFailed("登录已过期，请重新登录")

        return (token.user, token)
