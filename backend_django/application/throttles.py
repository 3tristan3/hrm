"""接口节流策略。"""
from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """登录接口限速（按 IP）。"""

    scope = "login"

    def get_rate(self):
        return getattr(settings, "AUTH_LOGIN_RATE", "10/min")

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}
