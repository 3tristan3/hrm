"""共享视图基础能力：导入、常量、通用工具与公共基类。"""

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

from ..authentication import ExpiringTokenAuthentication
from ..auth_security import (
    clear_login_failures,
    get_lock_remaining_seconds,
    normalize_login_username,
    register_login_failure,
)
from ..interview_flow import (
    FINAL_RESULTS,
    InterviewFlowError,
    MAX_INTERVIEW_ROUND,
    cancel_schedule,
    record_result,
    schedule_interview,
)
from ..audit import request_id_from_request, write_operation_log
from ..throttles import LoginRateThrottle
from ..operation_log_meta import (
    OPERATION_ACTION_LABELS,
    OPERATION_LOG_DEFAULT_DAYS,
    OPERATION_LOG_PAGE_SIZE_OPTIONS,
    OPERATION_MODULE_LABELS,
    OPERATION_RESULT_LABELS,
)
from ..recruitment_lifecycle import summarize_interview_outcomes
from ..models import (
    Application,
    ApplicationAttachment,
    InterviewCandidate,
    InterviewRoundRecord,
    Job,
    OperationLog,
    Region,
    RegionField,
)
from ..serializers import (
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
    InterviewCandidateBatchConfirmHireSerializer,
    InterviewCandidateCancelScheduleSerializer,
    InterviewCandidateListSerializer,
    InterviewPassedCandidateListSerializer,
    InterviewCandidateResultSerializer,
    InterviewCandidateResendSmsSerializer,
    InterviewCandidateScheduleSerializer,
    JobAdminSerializer,
    JobBatchStatusSerializer,
    JobSerializer,
    LoginSerializer,
    MeSerializer,
    PassedCandidateOfferStatusSerializer,
    PassedCandidateRetryOAPushSerializer,
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
User = get_user_model()


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
