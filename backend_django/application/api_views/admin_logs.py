"""按职责拆分的视图模块。"""
from .shared import *

def operation_log_base_queryset():
    """统一操作日志关联查询，避免列表/详情各自维护一套 select_related。"""
    return OperationLog.objects.select_related(
        "operator",
        "application",
        "application__region",
        "interview_candidate",
        "interview_candidate__application",
        "interview_candidate__application__region",
        "region",
    )

class AdminOperationLogListView(AdminScopedMixin, generics.ListAPIView):
    """管理端操作日志查询接口。"""

    serializer_class = OperationLogListSerializer
    pagination_class = OperationLogCursorPagination

    def get_queryset(self):
        queryset = operation_log_base_queryset()
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
        queryset = operation_log_base_queryset()
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
