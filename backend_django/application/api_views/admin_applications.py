"""按职责拆分的视图模块。"""
from .shared import *

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
