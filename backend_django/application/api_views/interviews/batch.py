"""面试域视图子模块。"""
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
