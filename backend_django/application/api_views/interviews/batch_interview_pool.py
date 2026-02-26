"""拟面试池批量动作接口。"""
from .shared import *


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
