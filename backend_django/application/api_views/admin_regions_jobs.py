"""按职责拆分的视图模块。"""
from .shared import *

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
        return self._scope_queryset(Job.objects.filter(is_deleted=False))

    def create(self, request: Request, *args, **kwargs):
        err = self._check_region_payload(request)
        if err:
            return err
        return super().create(request, *args, **kwargs)

class AdminJobDetailView(AdminScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(Job.objects.filter(is_deleted=False))

    def update(self, request: Request, *args, **kwargs):
        err = self._check_region_payload(request)
        if err:
            return err
        return super().update(request, *args, **kwargs)

    def destroy(self, request: Request, *args, **kwargs):
        job = self.get_object()
        candidates = InterviewCandidate.objects.filter(application__job_id=job.id).only(
            "status",
            "result",
            "is_hired",
        )
        outcome_summary = summarize_interview_outcomes(candidates)
        pending_count = outcome_summary["pending"]
        passed_count = outcome_summary["passed"]
        hired_count = outcome_summary["hired"]
        if pending_count > 0:
            return Response(
                {"error": f"该岗位仍有 {pending_count} 名在途候选人，无法删除"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if outcome_summary["total"] > 0 and hired_count <= 0:
            if passed_count > 0:
                error_message = f"该岗位有 {passed_count} 名面试通过人员未确认入职，无法删除"
            else:
                error_message = "该岗位尚未确认入职，无法删除"
            return Response(
                {"error": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_job_id = job.id
        target_job_title = job.title
        target_region = getattr(job, "region", None)
        job.is_active = False
        job.is_deleted = True
        job.deleted_at = timezone.now()
        job.save(update_fields=["is_active", "is_deleted", "deleted_at"])
        self._write_operation_log(
            request,
            user=request.user,
            module="jobs",
            action="DELETE_JOB",
            target_type="job",
            target_id=target_job_id,
            target_label=target_job_title,
            summary=f"删除岗位（逻辑删除）：{target_job_title}",
            details={
                "job_id": target_job_id,
                "title": target_job_title,
                "pending_count": pending_count,
                "passed_count": passed_count,
                "hired_count": hired_count,
                "talent_count": outcome_summary["talent"],
                "total_count": outcome_summary["total"],
            },
            region=target_region,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

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

        queryset = self._scope_queryset(Job.objects.filter(id__in=job_ids, is_deleted=False))
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
