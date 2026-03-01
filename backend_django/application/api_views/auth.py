"""按职责拆分的视图模块。"""
from .shared import *
from django.http import HttpResponseRedirect
from rest_framework import serializers

from ..oa_sso import (
    build_oa_sso_redirect_url,
    consume_oa_sso_login_ticket,
    create_oa_sso_login_ticket,
    is_oa_sso_appid_allowed,
    is_oa_sso_enabled,
    is_oa_sso_ip_allowed,
    merge_oa_sso_payload,
    oa_sso_ticket_ttl_seconds,
    pick_oa_sso_username,
    resolve_oa_sso_client_ip,
)

class RegisterView(APIView):
    def post(self, request: Request):
        return Response(
            {
                "error": "注册功能已关闭",
                "error_code": "REGISTER_DISABLED",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]

    @staticmethod
    def _locked_response(remaining_seconds: int) -> Response:
        retry_after_seconds = max(int(remaining_seconds), 1)
        retry_after_minutes = max((retry_after_seconds + 59) // 60, 1)
        return Response(
            {
                "error": "登录失败",
                "error_code": "LOGIN_LOCKED",
                "retry_after_seconds": retry_after_seconds,
                "details": {
                    "non_field_errors": [f"登录失败次数过多，请{retry_after_minutes}分钟后再试"]
                },
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def post(self, request: Request):
        username = normalize_login_username(request.data.get("username", ""))
        lock_remaining = get_lock_remaining_seconds(username)
        if lock_remaining > 0:
            return self._locked_response(lock_remaining)

        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            is_locked, remaining = register_login_failure(username)
            if is_locked:
                return self._locked_response(remaining)
            return Response(
                {"error": "登录失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.validated_data["user"]
        clear_login_failures(username)
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        profile = getattr(user, "profile", None)
        return Response(
            {
                "token": token.key,
                "username": user.username,
                "region": profile.region_id if profile else None,
                "can_view_all": profile.can_view_all if profile else False,
            }
        )


class OALoginExchangeSerializer(serializers.Serializer):
    ticket = serializers.CharField(max_length=128)


class OALoginEntryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def _handle(self, request: Request):
        if not is_oa_sso_enabled():
            return Response(
                {"error": "OA集成登录未启用", "error_code": "OA_SSO_DISABLED"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payload = merge_oa_sso_payload(request)
        appid = str(payload.get("appid") or "").strip()
        if not is_oa_sso_appid_allowed(appid):
            return Response(
                {"error": "OA应用标识不在允许范围内", "error_code": "OA_SSO_APPID_FORBIDDEN"},
                status=status.HTTP_403_FORBIDDEN,
            )

        client_ip = resolve_oa_sso_client_ip(request)
        if not is_oa_sso_ip_allowed(client_ip):
            return Response(
                {"error": "来源IP不在允许范围内", "error_code": "OA_SSO_IP_FORBIDDEN"},
                status=status.HTTP_403_FORBIDDEN,
            )

        username = normalize_login_username(pick_oa_sso_username(payload))
        if not username:
            return Response(
                {"error": "缺少OA账号参数", "error_code": "OA_SSO_USERNAME_REQUIRED"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        matched_user = User.objects.filter(username__iexact=username, is_active=True).first()
        if not matched_user:
            return Response(
                {"error": "HRM账号不存在或已禁用", "error_code": "OA_SSO_USER_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        ticket = create_oa_sso_login_ticket(
            user_id=matched_user.id,
            username=matched_user.username,
            appid=appid,
            source_ip=client_ip,
        )
        next_url = (
            str(payload.get("next") or "").strip()
            or str(payload.get("redirect_uri") or "").strip()
            or str(payload.get("return_url") or "").strip()
        )
        redirect_url = build_oa_sso_redirect_url(next_url, ticket=ticket)
        response_mode = str(payload.get("mode") or payload.get("response") or "").strip().lower()
        if response_mode == "json":
            return Response(
                {
                    "ticket": ticket,
                    "redirect_url": redirect_url,
                    "expires_in": oa_sso_ticket_ttl_seconds(),
                    "username": matched_user.username,
                }
            )
        return HttpResponseRedirect(redirect_url)

    def post(self, request: Request):
        return self._handle(request)

    def get(self, request: Request):
        return self._handle(request)


class OALoginExchangeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request: Request):
        if not is_oa_sso_enabled():
            return Response(
                {"error": "OA集成登录未启用", "error_code": "OA_SSO_DISABLED"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = OALoginExchangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket_payload = consume_oa_sso_login_ticket(serializer.validated_data["ticket"])
        if not ticket_payload:
            return Response(
                {"error": "OA登录票据无效或已过期", "error_code": "OA_SSO_TICKET_INVALID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = int(ticket_payload.get("user_id") or 0)
        user = User.objects.filter(pk=user_id, is_active=True).first()
        if not user:
            return Response(
                {"error": "HRM账号不存在或已禁用", "error_code": "OA_SSO_USER_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        profile = getattr(user, "profile", None)
        return Response(
            {
                "token": token.key,
                "username": user.username,
                "region": profile.region_id if profile else None,
                "can_view_all": profile.can_view_all if profile else False,
                "login_source": "oa_sso",
            }
        )

class MeView(APIView):
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        profile = getattr(request.user, "profile", None)
        serializer = MeSerializer(
            {
                "username": request.user.username,
                "is_superuser": request.user.is_superuser,
                "profile": profile,
            }
        )
        return Response(serializer.data)

class AdminUserListView(AdminScopedMixin, APIView):
    def get(self, request: Request):
        if not request.user.is_superuser:
            return Response({"error": "无权限访问"}, status=status.HTTP_403_FORBIDDEN)
        queryset = User.objects.select_related("profile__region").order_by("username")
        serializer = AdminUserSerializer(queryset, many=True)
        return Response(serializer.data)

class AdminUserPasswordView(AdminScopedMixin, APIView):
    def post(self, request: Request, pk: int):
        if not request.user.is_superuser:
            return Response({"error": "无权限操作"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=pk)
        serializer = AdminPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()
        self._write_operation_log(
            request,
            user=request.user,
            module="accounts",
            action="RESET_USER_PASSWORD",
            target_type="user",
            target_id=user.id,
            target_label=user.username,
            summary=f"重置账号密码：{user.username}",
            details={"user_id": user.id, "username": user.username},
            region=getattr(getattr(user, "profile", None), "region", None),
        )
        return Response({"message": "密码已更新"})

class AdminUserDetailView(AdminScopedMixin, APIView):
    def delete(self, request: Request, pk: int):
        if not request.user.is_superuser:
            return Response({"error": "无权限操作"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            return Response({"error": "不能删除系统管理员账号"}, status=status.HTTP_400_BAD_REQUEST)
        if user.pk == request.user.pk:
            return Response({"error": "不能删除当前登录账号"}, status=status.HTTP_400_BAD_REQUEST)
        target_id = user.id
        target_username = user.username
        target_region = getattr(getattr(user, "profile", None), "region", None)
        user.delete()
        self._write_operation_log(
            request,
            user=request.user,
            module="accounts",
            action="DELETE_USER",
            target_type="user",
            target_id=target_id,
            target_label=target_username,
            summary=f"删除账号：{target_username}",
            details={"user_id": target_id, "username": target_username},
            region=target_region,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

class ChangePasswordView(APIView):
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"error": "原密码不正确"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()
        return Response({"message": "密码已更新，请重新登录", "force_relogin": True})

class LogoutView(APIView):
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        token = getattr(request, "auth", None)
        if token:
            token.delete()
        else:
            Token.objects.filter(user=request.user).delete()
        return Response({"message": "已退出登录"})
