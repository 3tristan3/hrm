"""后端 API 视图实现，承载后台管理与应聘流程业务接口。"""
import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch, ProtectedError, Q
from django.shortcuts import get_object_or_404
from django.utils.crypto import constant_time_compare
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import ExpiringTokenAuthentication
from .auth_security import (
    clear_login_failures,
    get_lock_remaining_seconds,
    normalize_login_username,
    register_login_failure,
)
from .interview_flow import (
    FINAL_RESULTS,
    InterviewFlowError,
    MAX_INTERVIEW_ROUND,
    cancel_schedule,
    record_result,
    schedule_interview,
)
from .audit import request_id_from_request, write_operation_log
from .throttles import LoginRateThrottle
from .operation_log_meta import (
    OPERATION_ACTION_LABELS,
    OPERATION_LOG_DEFAULT_DAYS,
    OPERATION_LOG_PAGE_SIZE_OPTIONS,
    OPERATION_MODULE_LABELS,
    OPERATION_RESULT_LABELS,
)
from .models import (
    Application,
    ApplicationAttachment,
    InterviewCandidate,
    InterviewRoundRecord,
    Job,
    OperationLog,
    Region,
    RegionField,
)
from .serializers import (
    ApplicationAdminListSerializer,
    ApplicationAdminSerializer,
    ApplicationAttachmentSerializer,
    ApplicationAttachmentUploadSerializer,
    ApplicationCreateSerializer,
    AdminPasswordResetSerializer,
    AdminUserSerializer,
    ChangePasswordSerializer,
    InterviewCandidateBatchAddSerializer,
    InterviewCandidateBatchRemoveSerializer,
    InterviewCandidateCancelScheduleSerializer,
    InterviewCandidateListSerializer,
    InterviewPassedCandidateListSerializer,
    InterviewCandidateResultSerializer,
    InterviewCandidateScheduleSerializer,
    JobAdminSerializer,
    JobBatchStatusSerializer,
    JobSerializer,
    LoginSerializer,
    MeSerializer,
    OperationLogDetailSerializer,
    OperationLogListSerializer,
    OperationLogQuerySerializer,
    RegisterSerializer,
    RegionAdminSerializer,
    RegionFieldAdminSerializer,
    RegionSerializer,
)

MB_IN_BYTES = 1024 * 1024
ATTACHMENT_TOKEN_HEADER = "X-Application-Token"


def _safe_file_size(file_obj) -> int:
    try:
        return int(getattr(file_obj, "size", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _resolve_attachment_limits():
    max_file_mb = max(int(getattr(settings, "APPLICATION_ATTACHMENT_MAX_FILE_MB", 10) or 10), 1)
    max_total_mb = max(int(getattr(settings, "APPLICATION_ATTACHMENT_MAX_TOTAL_MB", 40) or 40), 1)
    return (
        max_file_mb,
        max_total_mb,
        max_file_mb * MB_IN_BYTES,
        max_total_mb * MB_IN_BYTES,
    )


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request):
        return Response({"status": "ok"})


class AdminResultListPagination(PageNumberPagination):
    """面试结果池分页器：默认每页 30 条，支持前端显式指定页大小。"""

    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100


class OperationLogCursorPagination(CursorPagination):
    """操作日志游标分页，避免深分页 offset 扫描。"""

    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = ("-created_at", "-id")


class AdminScopedMixin:
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _user_region_scope(self):
        user = self.request.user
        profile = getattr(user, "profile", None)
        if user.is_superuser:
            return None
        if profile and profile.can_view_all:
            return None
        return profile.region_id if profile else -1

    def _scope_queryset(self, queryset):
        region_id = self._user_region_scope()
        if region_id:
            return queryset.filter(region_id=region_id)
        return queryset

    def _check_region_payload(self, request):
        """校验非全局账号只能操作所属地区的数据，返回 Response 或 None。"""
        region_id = self._user_region_scope()
        if region_id is None:
            return None
        payload_region = request.data.get("region")
        try:
            payload_region = int(payload_region)
        except (TypeError, ValueError):
            payload_region = None
        if payload_region != region_id:
            return Response(
                {"error": "只能维护所属地区的岗位"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def _write_operation_log(self, request: Request, **kwargs):
        """统一封装审计写入，避免在各视图重复传 request_id。"""
        write_operation_log(
            request_id=request_id_from_request(request),
            **kwargs,
        )


class RegionListView(APIView):
    def get(self, request: Request):
        queryset = Region.objects.filter(is_active=True).prefetch_related("fields")
        serializer = RegionSerializer(queryset, many=True)
        return Response(serializer.data)


class JobListView(APIView):
    def get(self, request: Request):
        queryset = Job.objects.filter(is_active=True)
        region_id = request.query_params.get("region_id")
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        serializer = JobSerializer(queryset, many=True)
        return Response(serializer.data)


class JobDetailView(APIView):
    def get(self, request: Request, pk: int):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        serializer = JobSerializer(job)
        return Response(serializer.data)


class ApplicationCreateView(APIView):
    def _coerce_payload(self, data):
        payload = data.copy() if hasattr(data, "copy") else dict(data)
        for key in ("education_history", "work_history", "family_members", "extra_fields"):
            value = payload.get(key)
            if isinstance(value, str):
                try:
                    payload[key] = json.loads(value)
                except json.JSONDecodeError:
                    pass
        for key in ("available_date", "birth_month", "graduation_date"):
            if payload.get(key) == "":
                payload[key] = None
        return payload

    def post(self, request: Request):
        payload = self._coerce_payload(request.data)
        serializer = ApplicationCreateSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        # region / job 由 validate() 写入，region_id / job_id 是序列化器字段不需要
        create_kwargs = {k: v for k, v in data.items() if k not in ("region_id", "job_id")}
        application = Application.objects.create(**create_kwargs)

        return Response(
            {
                "message": "提交成功",
                "applicationId": application.pk,
                "attachmentToken": application.attachment_token,
            },
            status=status.HTTP_201_CREATED,
        )


class ApplicationSubmitView(ApplicationCreateView):
    pass


class MockOAView(APIView):
    def post(self, request: Request):
        payload = request.data
        return Response(
            {
                "requestId": "MOCK-REQUEST-001",
                "received": payload,
            },
            status=status.HTTP_201_CREATED,
        )


class ApplicationTokenAccessMixin:
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [AllowAny]

    @staticmethod
    def _not_found_response():
        return Response({"error": "记录不存在"}, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def _is_admin_request(request: Request) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)

    @staticmethod
    def _extract_token(request: Request):
        header_value = (request.headers.get(ATTACHMENT_TOKEN_HEADER) or "").strip()
        if header_value:
            return header_value
        query_value = (request.query_params.get("token") or "").strip()
        if query_value:
            return query_value
        data_value = (request.data.get("attachment_token") or "").strip() if hasattr(request, "data") else ""
        return data_value

    def _has_valid_token(self, request: Request, application: Application) -> bool:
        token = self._extract_token(request)
        if not token:
            return False
        return constant_time_compare(str(application.attachment_token), token)

    def _resolve_accessible_application(self, request: Request, pk: int):
        application = get_object_or_404(Application, pk=pk)
        if self._is_admin_request(request) or self._has_valid_token(request, application):
            return application
        return None


class ApplicationAttachmentListCreateView(ApplicationTokenAccessMixin, APIView):
    def get(self, request: Request, pk: int):
        application = self._resolve_accessible_application(request, pk)
        if not application:
            return self._not_found_response()
        serializer = ApplicationAttachmentSerializer(
            application.attachments.all(), many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request: Request, pk: int):
        application = self._resolve_accessible_application(request, pk)
        if not application:
            return self._not_found_response()
        serializer = ApplicationAttachmentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        category = serializer.validated_data["category"]
        files = request.FILES.getlist("file")
        if not files:
            return Response(
                {"error": "未上传文件"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if category != "other" and len(files) > 1:
            return Response(
                {"error": "该附件类型仅支持上传单个文件"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_file_mb, max_total_mb, max_file_bytes, max_total_bytes = _resolve_attachment_limits()
        oversized_files = [upload.name for upload in files if _safe_file_size(upload) > max_file_bytes]
        if oversized_files:
            return Response(
                {
                    "error": f"单个文件不能超过{max_file_mb}MB",
                    "details": {"file": [f"超出大小限制: {name}" for name in oversized_files]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        incoming_total_bytes = sum(_safe_file_size(upload) for upload in files)
        existing_attachments = list(application.attachments.all())
        existing_total_bytes = sum(_safe_file_size(item.file) for item in existing_attachments)
        replaced_bytes = 0
        if category != "other":
            replaced_bytes = sum(
                _safe_file_size(item.file) for item in existing_attachments if item.category == category
            )
        projected_total_bytes = max(existing_total_bytes - replaced_bytes, 0) + incoming_total_bytes
        if projected_total_bytes > max_total_bytes:
            return Response(
                {"error": f"附件总大小不能超过{max_total_mb}MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if category != "other":
            ApplicationAttachment.objects.filter(
                application=application, category=category
            ).delete()
        attachments = [
            ApplicationAttachment.objects.create(
                application=application, category=category, file=upload
            )
            for upload in files
        ]
        output = ApplicationAttachmentSerializer(
            attachments, many=True, context={"request": request}
        )
        return Response(output.data, status=status.HTTP_201_CREATED)


class ApplicationDiscardView(ApplicationTokenAccessMixin, APIView):
    def post(self, request: Request, pk: int):
        application = self._resolve_accessible_application(request, pk)
        if not application:
            return self._not_found_response()
        if hasattr(application, "interview_candidate"):
            return Response(
                {"error": "记录已进入面试流程，无法撤销"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            for item in application.attachments.all():
                try:
                    item.file.delete(save=False)
                except Exception:
                    pass
            application.delete()
        return Response({"message": "草稿已撤销"})


class RegisterView(APIView):
    def post(self, request: Request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = serializer.save()
        return Response(
            {
                "token": result["token"],
                "username": result["user"].username,
                "region": result["region"].id,
                "can_view_all": result["can_view_all"],
            },
            status=status.HTTP_201_CREATED,
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


User = get_user_model()


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


class _RegionAdminQuerysetMixin(AdminScopedMixin):
    """共享 Region 查询集逻辑。"""
    serializer_class = RegionAdminSerializer

    def get_queryset(self):
        region_id = self._user_region_scope()
        if region_id:
            return Region.objects.filter(id=region_id)
        return Region.objects.all()


class AdminRegionListView(_RegionAdminQuerysetMixin, generics.ListCreateAPIView):

    def create(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区为系统固定配置，无法新增"},
            status=status.HTTP_403_FORBIDDEN,
        )


class AdminRegionDetailView(_RegionAdminQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):

    def update(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区为系统固定配置，无法修改"},
            status=status.HTTP_403_FORBIDDEN,
        )

    def destroy(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区为系统固定配置，无法删除"},
            status=status.HTTP_403_FORBIDDEN,
        )


class AdminRegionFieldListView(AdminScopedMixin, generics.ListCreateAPIView):
    queryset = RegionField.objects.all()
    serializer_class = RegionFieldAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(RegionField.objects.all())

    def create(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区字段为系统固定配置，无法新增"},
            status=status.HTTP_403_FORBIDDEN,
        )


class AdminRegionFieldDetailView(AdminScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = RegionField.objects.all()
    serializer_class = RegionFieldAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(RegionField.objects.all())

    def update(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区字段为系统固定配置，无法修改"},
            status=status.HTTP_403_FORBIDDEN,
        )

    def destroy(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区字段为系统固定配置，无法删除"},
            status=status.HTTP_403_FORBIDDEN,
        )


class AdminJobListView(AdminScopedMixin, generics.ListCreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(Job.objects.all())

    def create(self, request: Request, *args, **kwargs):
        err = self._check_region_payload(request)
        if err:
            return err
        return super().create(request, *args, **kwargs)


class AdminJobDetailView(AdminScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(Job.objects.all())

    def update(self, request: Request, *args, **kwargs):
        err = self._check_region_payload(request)
        if err:
            return err
        return super().update(request, *args, **kwargs)

    def destroy(self, request: Request, *args, **kwargs):
        job = self.get_object()
        target_job_id = job.id
        target_job_title = job.title
        target_region = getattr(job, "region", None)
        try:
            response = super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "该岗位已有应聘记录，无法删除"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self._write_operation_log(
            request,
            user=request.user,
            module="jobs",
            action="DELETE_JOB",
            target_type="job",
            target_id=target_job_id,
            target_label=target_job_title,
            summary=f"删除岗位：{target_job_title}",
            details={"job_id": target_job_id, "title": target_job_title},
            region=target_region,
        )
        return response


class AdminJobBatchStatusView(AdminScopedMixin, APIView):
    def post(self, request: Request):
        serializer = JobBatchStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job_ids = serializer.validated_data["job_ids"]
        is_active = serializer.validated_data["is_active"]

        queryset = self._scope_queryset(Job.objects.filter(id__in=job_ids))
        allowed_ids = set(queryset.values_list("id", flat=True))
        missing_ids = sorted(set(job_ids) - allowed_ids)
        if missing_ids:
            return Response(
                {
                    "error": "包含无权限或不存在的岗位",
                    "details": {"job_ids": missing_ids},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = queryset.update(is_active=is_active)
        action = "BATCH_DEACTIVATE_JOB" if not is_active else "BATCH_ACTIVATE_JOB"
        self._write_operation_log(
            request,
            user=request.user,
            module="jobs",
            action=action,
            target_type="job_batch",
            target_label=f"{len(job_ids)}个岗位",
            summary=f"{'下架' if not is_active else '上架'}岗位 {updated} 个",
            details={
                "job_ids": job_ids,
                "updated": updated,
                "total": len(job_ids),
                "is_active": is_active,
            },
        )
        return Response(
            {
                "updated": updated,
                "total": len(job_ids),
                "is_active": is_active,
            }
        )


class _ApplicationAdminQuerysetMixin(AdminScopedMixin):
    """共享 Application 查询集逻辑。"""

    def get_queryset(self):
        queryset = Application.objects.select_related("region", "job").prefetch_related(
            Prefetch(
                "attachments",
                queryset=ApplicationAttachment.objects.filter(category="photo").order_by("-created_at"),
                to_attr="photo_attachments",
            )
        )
        return self._scope_queryset(queryset)


class AdminApplicationListView(_ApplicationAdminQuerysetMixin, generics.ListAPIView):
    serializer_class = ApplicationAdminListSerializer

    def get_queryset(self):
        # 应聘记录列表仅展示尚未进入拟面试池的记录。
        # 一旦加入拟面试池（存在 interview_candidate），就从该列表移除；
        # 若后续从拟面试池移除（删除 interview_candidate），会自动重新出现。
        queryset = super().get_queryset().filter(
            job__is_active=True,
            interview_candidate__isnull=True,
        )
        job_id = self.request.query_params.get("job_id")
        region_id = self.request.query_params.get("region_id")
        job = self.request.query_params.get("job")
        region = self.request.query_params.get("region")
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if job:
            queryset = queryset.filter(job__title__icontains=job)
        if region:
            queryset = queryset.filter(region__name__icontains=region)
        return queryset


class AdminApplicationDetailView(_ApplicationAdminQuerysetMixin, generics.RetrieveAPIView):
    serializer_class = ApplicationAdminSerializer


class _InterviewCandidateAdminQuerysetMixin(AdminScopedMixin):
    """拟面试人员模块共用能力：查询范围、行锁读取、流程错误输出。"""

    def get_queryset(self):
        """返回带应聘信息的候选人列表，并按账号地区做数据隔离。"""
        queryset = InterviewCandidate.objects.select_related(
            "application",
            "application__region",
            "application__job",
        ).prefetch_related(
            Prefetch(
                "application__attachments",
                queryset=ApplicationAttachment.objects.filter(category="photo").order_by(
                    "-created_at"
                ),
                to_attr="photo_attachments",
            )
        )
        region_id = self._user_region_scope()
        if region_id:
            queryset = queryset.filter(application__region_id=region_id)
        return queryset

    def get_locked_candidate(self, pk: int) -> InterviewCandidate:
        """在事务中读取并锁定候选人，避免并发写导致状态错乱。"""
        queryset = InterviewCandidate.objects.select_for_update().select_related(
            "application",
            "application__region",
            "application__job",
        )
        region_id = self._user_region_scope()
        if region_id:
            queryset = queryset.filter(application__region_id=region_id)
        return get_object_or_404(queryset, pk=pk)

    @staticmethod
    def flow_error_response(error: InterviewFlowError) -> Response:
        """统一输出流程层业务错误。"""
        return Response(error.to_payload(), status=error.status_code)


class AdminInterviewCandidateListView(_InterviewCandidateAdminQuerysetMixin, generics.ListAPIView):
    serializer_class = InterviewCandidateListSerializer

    def get_queryset(self):
        # 拟面试池仅展示流程中的候选人，已出结果（已完成）移出该列表。
        return super().get_queryset().exclude(status=InterviewCandidate.STATUS_COMPLETED)


class AdminInterviewMetaView(AdminScopedMixin, APIView):
    """输出面试模块元数据，供前端统一常量和选项。"""

    def get(self, request: Request):
        return Response(
            {
                "status_pending": InterviewCandidate.STATUS_PENDING,
                "status_scheduled": InterviewCandidate.STATUS_SCHEDULED,
                "status_completed": InterviewCandidate.STATUS_COMPLETED,
                "result_pending": InterviewCandidate.RESULT_PENDING,
                "result_next_round": InterviewCandidate.RESULT_NEXT_ROUND,
                "result_pass": InterviewCandidate.RESULT_PASS,
                "result_reject": InterviewCandidate.RESULT_REJECT,
                "status_choices": [
                    {"value": value, "label": label}
                    for value, label in InterviewCandidate.STATUS_CHOICES
                ],
                "result_choices": [
                    {"value": value, "label": label}
                    for value, label in InterviewCandidate.RESULT_CHOICES
                ],
                "final_results": list(FINAL_RESULTS),
                "max_round": MAX_INTERVIEW_ROUND,
            }
        )


class _InterviewOutcomeCandidateListView(_InterviewCandidateAdminQuerysetMixin, generics.ListAPIView):
    """面试结果池列表基类：按最终结果筛选并输出轮次快照。"""

    serializer_class = InterviewPassedCandidateListSerializer
    pagination_class = AdminResultListPagination
    outcome_result: str = ""

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            status=InterviewCandidate.STATUS_COMPLETED,
            result=self.outcome_result,
        )
        return queryset.prefetch_related(
            Prefetch(
                "round_records",
                queryset=InterviewRoundRecord.objects.order_by("round_no", "id"),
            )
        ).order_by("-result_at", "-updated_at", "-id")

    def list(self, request: Request, *args, **kwargs):
        """兼容历史返回：仅当前端传 page/page_size 时启用分页结构。"""
        if "page" not in request.query_params and "page_size" not in request.query_params:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)


class AdminOperationLogListView(AdminScopedMixin, generics.ListAPIView):
    """管理端操作日志查询接口。"""

    serializer_class = OperationLogListSerializer
    pagination_class = OperationLogCursorPagination

    def get_queryset(self):
        queryset = OperationLog.objects.select_related(
            "operator",
            "application",
            "application__region",
            "interview_candidate",
            "interview_candidate__application",
            "interview_candidate__application__region",
            "region",
        )
        region_id = self._user_region_scope()
        if region_id:
            # 以业务对象所属地区做隔离；region 字段作为无关联业务对象时的兜底。
            queryset = queryset.filter(
                Q(application__region_id=region_id)
                | Q(interview_candidate__application__region_id=region_id)
                | Q(region_id=region_id)
            )

        query_serializer = OperationLogQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        if params.get("application_id"):
            queryset = queryset.filter(application_id=params["application_id"])
        if params.get("operator_id"):
            queryset = queryset.filter(operator_id=params["operator_id"])
        if params.get("operator"):
            queryset = queryset.filter(operator_username__icontains=params["operator"])
        if params.get("module"):
            queryset = queryset.filter(module=params["module"])
        if params.get("action"):
            queryset = queryset.filter(action=params["action"])
        if params.get("result"):
            queryset = queryset.filter(result=params["result"])
        if params.get("date_from"):
            queryset = queryset.filter(created_at__date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(created_at__date__lte=params["date_to"])
        if not params.get("application_id") and not params.get("date_from") and not params.get("date_to"):
            recent_date = timezone.localdate() - timedelta(days=OPERATION_LOG_DEFAULT_DAYS)
            queryset = queryset.filter(created_at__date__gte=recent_date)
        if params.get("keyword"):
            keyword = params["keyword"]
            queryset = queryset.filter(
                Q(operator_username__icontains=keyword)
                | Q(target_label__icontains=keyword)
                | Q(summary__icontains=keyword)
            )
        return queryset.order_by("-created_at", "-id")


class AdminOperationLogDetailView(AdminScopedMixin, generics.RetrieveAPIView):
    """操作日志详情接口（按需返回 details）。"""

    serializer_class = OperationLogDetailSerializer

    def get_queryset(self):
        queryset = OperationLog.objects.select_related(
            "operator",
            "application",
            "application__region",
            "interview_candidate",
            "interview_candidate__application",
            "interview_candidate__application__region",
            "region",
        )
        region_id = self._user_region_scope()
        if region_id:
            queryset = queryset.filter(
                Q(application__region_id=region_id)
                | Q(interview_candidate__application__region_id=region_id)
                | Q(region_id=region_id)
            )
        return queryset


class AdminOperationLogMetaView(AdminScopedMixin, APIView):
    """管理端操作日志元信息：标签映射与分页配置。"""

    def get(self, request: Request):
        return Response(
            {
                "module_labels": OPERATION_MODULE_LABELS,
                "action_labels": OPERATION_ACTION_LABELS,
                "result_labels": OPERATION_RESULT_LABELS,
                "page_size_options": OPERATION_LOG_PAGE_SIZE_OPTIONS,
                "default_recent_days": OPERATION_LOG_DEFAULT_DAYS,
                "pagination_mode": "cursor",
            }
        )


class AdminPassedCandidateListView(_InterviewOutcomeCandidateListView):
    """面试通过人员列表，含各轮次快照信息。"""

    outcome_result = InterviewCandidate.RESULT_PASS


class AdminTalentPoolCandidateListView(_InterviewOutcomeCandidateListView):
    """人才库列表（面试淘汰人员），含各轮次快照信息。"""

    outcome_result = InterviewCandidate.RESULT_REJECT


class AdminInterviewCandidateDetailView(
    _InterviewCandidateAdminQuerysetMixin, generics.DestroyAPIView
):
    serializer_class = InterviewCandidateListSerializer

    def destroy(self, request: Request, *args, **kwargs):
        candidate = self.get_object()
        application = candidate.application
        candidate_id = candidate.id
        response = super().destroy(request, *args, **kwargs)
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="REMOVE_FROM_INTERVIEW_POOL",
            target_type="interview_candidate",
            target_id=candidate_id,
            target_label=application.name,
            summary=f"移出拟面试人员：{application.name}",
            details={"interview_candidate_id": candidate_id, "application_id": application.id},
            application=application,
            region=application.region,
        )
        return response


class AdminInterviewCandidateScheduleView(_InterviewCandidateAdminQuerysetMixin, APIView):
    """安排/改期面试接口。"""

    def post(self, request: Request, pk: int):
        serializer = InterviewCandidateScheduleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        was_scheduled = False
        before_round = 1
        candidate = None
        try:
            with transaction.atomic():
                candidate = self.get_locked_candidate(pk)
                before_round = max(int(candidate.interview_round or 1), 1)
                was_scheduled = bool(candidate.interview_at) or candidate.status == InterviewCandidate.STATUS_SCHEDULED
                schedule_interview(
                    candidate,
                    interview_at=data["interview_at"],
                    interviewer=data.get("interviewer", ""),
                    interview_location=data.get("interview_location", ""),
                    note=data.get("note", None),
                )
        except InterviewFlowError as err:
            return self.flow_error_response(err)

        action = "RESCHEDULE_INTERVIEW" if was_scheduled else "SCHEDULE_INTERVIEW"
        application = candidate.application
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action=action,
            target_type="interview_candidate",
            target_id=candidate.id,
            target_label=application.name,
            summary=f"{'改期安排' if was_scheduled else '安排面试'}：{application.name}",
            details={
                "before_round": before_round,
                "current_round": candidate.interview_round,
                "interview_at": candidate.interview_at.isoformat() if candidate.interview_at else "",
                "interviewer": candidate.interviewer,
                "interview_location": candidate.interview_location,
            },
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewCandidateListSerializer(candidate, context={"request": request})
        return Response({"message": "面试安排已保存", "candidate": output.data})


class AdminInterviewCandidateCancelScheduleView(_InterviewCandidateAdminQuerysetMixin, APIView):
    """取消已安排面试接口。"""

    def post(self, request: Request, pk: int):
        serializer = InterviewCandidateCancelScheduleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                candidate = self.get_locked_candidate(pk)
                cancel_schedule(
                    candidate,
                    note=serializer.validated_data.get("note", "").strip(),
                )
        except InterviewFlowError as err:
            return self.flow_error_response(err)

        application = candidate.application
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="CANCEL_INTERVIEW_SCHEDULE",
            target_type="interview_candidate",
            target_id=candidate.id,
            target_label=application.name,
            summary=f"取消面试安排：{application.name}",
            details={"interview_candidate_id": candidate.id, "application_id": application.id},
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewCandidateListSerializer(candidate, context={"request": request})
        return Response({"message": "已取消面试安排", "candidate": output.data})


class AdminInterviewCandidateResultView(_InterviewCandidateAdminQuerysetMixin, APIView):
    """记录面试结果并推进到下一状态。"""

    def post(self, request: Request, pk: int):
        serializer = InterviewCandidateResultSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        result = data["result"]
        score = data.get("score", None)
        result_note = data.get("result_note", "")

        try:
            with transaction.atomic():
                candidate = self.get_locked_candidate(pk)
                record_result(
                    candidate,
                    result=result,
                    score=score,
                    result_note=result_note,
                )
        except InterviewFlowError as err:
            return self.flow_error_response(err)

        application = candidate.application
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="SAVE_INTERVIEW_RESULT",
            target_type="interview_candidate",
            target_id=candidate.id,
            target_label=application.name,
            summary=f"记录面试结果：{application.name}",
            details={
                "interview_candidate_id": candidate.id,
                "application_id": application.id,
                "round": candidate.interview_round,
                "result": candidate.result,
                "score": candidate.score,
            },
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewCandidateListSerializer(candidate, context={"request": request})
        return Response({"message": "面试结果已保存", "candidate": output.data})


class AdminInterviewCandidateBatchAddView(AdminScopedMixin, APIView):
    """批量把应聘记录加入拟面试池。"""

    def post(self, request: Request):
        serializer = InterviewCandidateBatchAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application_ids = serializer.validated_data["application_ids"]
        region_id = self._user_region_scope()
        app_queryset = Application.objects.select_related("region").filter(id__in=application_ids)
        if region_id:
            app_queryset = app_queryset.filter(region_id=region_id)

        allowed_ids = set(app_queryset.values_list("id", flat=True))
        missing_ids = sorted(set(application_ids) - allowed_ids)
        if missing_ids:
            return Response(
                {
                    "error": "包含无权限或不存在的应聘记录",
                    "details": {"application_ids": missing_ids},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_before = set(
            InterviewCandidate.objects.filter(application_id__in=application_ids).values_list(
                "application_id", flat=True
            )
        )

        to_create = [
            InterviewCandidate(application_id=application_id)
            for application_id in application_ids
            if application_id not in existing_before
        ]
        if to_create:
            InterviewCandidate.objects.bulk_create(to_create, ignore_conflicts=True)

        existing_after = set(
            InterviewCandidate.objects.filter(application_id__in=application_ids).values_list(
                "application_id", flat=True
            )
        )
        added_count = len(existing_after - existing_before)
        app_map = {app.id: app for app in app_queryset}
        for application_id in application_ids:
            application = app_map.get(application_id)
            if not application:
                continue
            is_existing = application_id in existing_before
            self._write_operation_log(
                request,
                user=request.user,
                module="applications",
                action="ADD_TO_INTERVIEW_POOL",
                target_type="application",
                target_id=application.id,
                target_label=application.name,
                summary=f"{application.name}加入拟面试人员{'（已存在）' if is_existing else ''}",
                details={
                    "application_id": application.id,
                    "existing": is_existing,
                    "added": not is_existing,
                },
                application=application,
                region=application.region,
            )
        self._write_operation_log(
            request,
            user=request.user,
            module="applications",
            action="BATCH_ADD_TO_INTERVIEW_POOL",
            target_type="application_batch",
            target_label=f"{len(application_ids)}条应聘记录",
            summary=f"批量加入拟面试人员：新增 {added_count}，已存在 {len(existing_before)}",
            details={
                "application_ids": application_ids,
                "added": added_count,
                "existing": len(existing_before),
                "total": len(application_ids),
            },
        )

        return Response(
            {
                "added": added_count,
                "existing": len(existing_before),
                "total": len(application_ids),
            }
        )


class AdminInterviewCandidateBatchRemoveView(AdminScopedMixin, APIView):
    """批量从拟面试池移除候选人。"""

    def post(self, request: Request):
        serializer = InterviewCandidateBatchRemoveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        interview_candidate_ids = serializer.validated_data["interview_candidate_ids"]
        queryset = InterviewCandidate.objects.filter(id__in=interview_candidate_ids)
        region_id = self._user_region_scope()
        if region_id:
            queryset = queryset.filter(application__region_id=region_id)

        allowed_ids = set(queryset.values_list("id", flat=True))
        missing_ids = sorted(set(interview_candidate_ids) - allowed_ids)
        if missing_ids:
            return Response(
                {
                    "error": "包含无权限或不存在的拟面试人员记录",
                    "details": {"interview_candidate_ids": missing_ids},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        removing_candidates = list(
            queryset.select_related("application", "application__region")
        )
        removed_count = len(removing_candidates)
        queryset.delete()
        for candidate in removing_candidates:
            application = candidate.application
            self._write_operation_log(
                request,
                user=request.user,
                module="interviews",
                action="REMOVE_FROM_INTERVIEW_POOL",
                target_type="interview_candidate",
                target_id=candidate.id,
                target_label=application.name,
                summary=f"移出拟面试人员：{application.name}",
                details={"interview_candidate_id": candidate.id, "application_id": application.id},
                application=application,
                region=application.region,
            )
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="BATCH_REMOVE_FROM_INTERVIEW_POOL",
            target_type="interview_candidate_batch",
            target_label=f"{len(interview_candidate_ids)}名候选人",
            summary=f"批量移出拟面试人员：{removed_count} 人",
            details={
                "interview_candidate_ids": interview_candidate_ids,
                "removed": removed_count,
                "total": len(interview_candidate_ids),
            },
        )
        return Response(
            {
                "removed": removed_count,
                "total": len(interview_candidate_ids),
            }
        )


class AdminTalentPoolCandidateBatchAddView(AdminScopedMixin, APIView):
    """批量把应聘记录直接加入人才库（淘汰池）。"""

    def post(self, request: Request):
        serializer = InterviewCandidateBatchAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application_ids = serializer.validated_data["application_ids"]
        region_id = self._user_region_scope()
        app_queryset = Application.objects.select_related("region").filter(id__in=application_ids)
        if region_id:
            app_queryset = app_queryset.filter(region_id=region_id)

        allowed_ids = set(app_queryset.values_list("id", flat=True))
        missing_ids = sorted(set(application_ids) - allowed_ids)
        if missing_ids:
            return Response(
                {
                    "error": "包含无权限或不存在的应聘记录",
                    "details": {"application_ids": missing_ids},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        moved = 0
        existing = 0
        blocked_ids = []
        default_note = "简历初筛未通过"
        moved_ids = set()
        existing_ids = set()

        with transaction.atomic():
            candidates = {
                item.application_id: item
                for item in InterviewCandidate.objects.select_for_update().filter(
                    application_id__in=application_ids
                )
            }
            for app_id in application_ids:
                candidate = candidates.get(app_id)
                if candidate is None:
                    InterviewCandidate.objects.create(
                        application_id=app_id,
                        status=InterviewCandidate.STATUS_COMPLETED,
                        result=InterviewCandidate.RESULT_REJECT,
                        result_at=now,
                        note=default_note,
                    )
                    moved += 1
                    moved_ids.add(app_id)
                    continue

                if (
                    candidate.status == InterviewCandidate.STATUS_COMPLETED
                    and candidate.result == InterviewCandidate.RESULT_PASS
                ):
                    blocked_ids.append(app_id)
                    continue

                if (
                    candidate.status == InterviewCandidate.STATUS_COMPLETED
                    and candidate.result == InterviewCandidate.RESULT_REJECT
                ):
                    existing += 1
                    existing_ids.add(app_id)
                    continue

                candidate.status = InterviewCandidate.STATUS_COMPLETED
                candidate.result = InterviewCandidate.RESULT_REJECT
                candidate.result_at = now
                candidate.interview_at = None
                candidate.interviewer = ""
                candidate.interview_location = ""
                candidate.score = None
                candidate.result_note = candidate.result_note or ""
                candidate.note = candidate.note or default_note
                candidate.save(
                    update_fields=[
                        "status",
                        "result",
                        "result_at",
                        "interview_at",
                        "interviewer",
                        "interview_location",
                        "score",
                        "result_note",
                        "note",
                        "updated_at",
                    ]
                )
                moved += 1
                moved_ids.add(app_id)

        app_map = {app.id: app for app in app_queryset}
        blocked_set = set(blocked_ids)
        for application_id in application_ids:
            application = app_map.get(application_id)
            if not application:
                continue
            if application_id in blocked_set:
                result_value = OperationLog.RESULT_FAILED
                summary = f"{application.name}加入人才库失败：候选人已通过"
            elif application_id in existing_ids:
                result_value = OperationLog.RESULT_SUCCESS
                summary = f"{application.name}加入人才库（已在人才库）"
            elif application_id in moved_ids:
                result_value = OperationLog.RESULT_SUCCESS
                summary = f"{application.name}加入人才库（简历初筛未通过）"
            else:
                result_value = OperationLog.RESULT_FAILED
                summary = f"{application.name}加入人才库失败"

            self._write_operation_log(
                request,
                user=request.user,
                module="applications",
                action="ADD_TO_TALENT_POOL",
                result=result_value,
                target_type="application",
                target_id=application.id,
                target_label=application.name,
                summary=summary,
                details={
                    "application_id": application.id,
                    "moved": application_id in moved_ids,
                    "existing": application_id in existing_ids,
                    "blocked": application_id in blocked_set,
                },
                application=application,
                region=application.region,
            )

        self._write_operation_log(
            request,
            user=request.user,
            module="applications",
            action="BATCH_ADD_TO_TALENT_POOL",
            target_type="application_batch",
            target_label=f"{len(application_ids)}条应聘记录",
            summary=f"批量加入人才库（简历初筛未通过）：加入 {moved}，已在库 {existing}，拦截 {len(blocked_ids)}",
            details={
                "application_ids": application_ids,
                "moved": moved,
                "existing": existing,
                "blocked": len(blocked_ids),
                "blocked_application_ids": blocked_ids,
                "total": len(application_ids),
            },
        )

        return Response(
            {
                "moved": moved,
                "existing": existing,
                "blocked": len(blocked_ids),
                "blocked_application_ids": blocked_ids,
                "total": len(application_ids),
            }
        )


class AdminTalentPoolCandidateBatchToInterviewView(AdminScopedMixin, APIView):
    """批量把人才库候选人重新加入拟面试人员。"""

    def post(self, request: Request):
        serializer = InterviewCandidateBatchRemoveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        interview_candidate_ids = serializer.validated_data["interview_candidate_ids"]
        region_id = self._user_region_scope()

        with transaction.atomic():
            queryset = InterviewCandidate.objects.select_for_update().filter(
                id__in=interview_candidate_ids,
                status=InterviewCandidate.STATUS_COMPLETED,
                result=InterviewCandidate.RESULT_REJECT,
            )
            if region_id:
                queryset = queryset.filter(application__region_id=region_id)

            allowed_ids = set(queryset.values_list("id", flat=True))
            missing_ids = sorted(set(interview_candidate_ids) - allowed_ids)
            if missing_ids:
                return Response(
                    {
                        "error": "包含无权限、不存在或非人才库状态的记录",
                        "details": {"interview_candidate_ids": missing_ids},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            moving_candidates = list(
                queryset.select_related("application", "application__region")
            )
            moved = len(moving_candidates)

            # 直接复位原记录，避免删除重建导致候选人ID变化。
            queryset.update(
                status=InterviewCandidate.STATUS_PENDING,
                interview_round=1,
                interview_at=None,
                interviewer="",
                interview_location="",
                result="",
                score=None,
                result_note="",
                result_at=None,
                note="",
                updated_at=timezone.now(),
            )

        for candidate in moving_candidates:
            application = candidate.application
            self._write_operation_log(
                request,
                user=request.user,
                module="talent",
                action="MOVE_TALENT_TO_INTERVIEW",
                target_type="interview_candidate",
                target_id=candidate.id,
                target_label=application.name,
                summary=f"{application.name}从人才库加入拟面试人员",
                details={"interview_candidate_id": candidate.id, "application_id": application.id},
                application=application,
                region=application.region,
            )
        self._write_operation_log(
            request,
            user=request.user,
            module="talent",
            action="BATCH_MOVE_TALENT_TO_INTERVIEW",
            target_type="interview_candidate_batch",
            target_label=f"{len(interview_candidate_ids)}名候选人",
            summary=f"批量从人才库加入拟面试人员：{moved} 人",
            details={
                "interview_candidate_ids": interview_candidate_ids,
                "moved": moved,
                "total": len(interview_candidate_ids),
            },
        )

        return Response(
            {
                "moved": moved,
                "total": len(interview_candidate_ids),
            }
        )
