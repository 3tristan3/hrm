"""面试确认入职视图子模块。"""
from .shared import *
from ...hire_integration import dispatch_hire_confirmation


class AdminPassedCandidateBatchConfirmHireView(AdminScopedMixin, APIView):
    """批量确认面试通过人员入职。"""

    def post(self, request: Request):
        serializer = InterviewCandidateBatchConfirmHireSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        interview_candidate_ids = serializer.validated_data["interview_candidate_ids"]
        push_targets = serializer.validated_data.get("push_targets", [])
        region_id = self._user_region_scope()

        with transaction.atomic():
            queryset = InterviewCandidate.objects.select_for_update().select_related(
                "application",
                "application__region",
            ).filter(id__in=interview_candidate_ids)
            if region_id:
                queryset = queryset.filter(application__region_id=region_id)

            candidate_map = {item.id: item for item in queryset}
            missing_ids = sorted(set(interview_candidate_ids) - set(candidate_map.keys()))
            if missing_ids:
                return Response(
                    {
                        "error": "包含无权限或不存在的面试通过人员",
                        "details": {"interview_candidate_ids": missing_ids},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            invalid_state_ids = []
            for candidate_id in interview_candidate_ids:
                candidate = candidate_map[candidate_id]
                if (
                    candidate.status != InterviewCandidate.STATUS_COMPLETED
                    or candidate.result != InterviewCandidate.RESULT_PASS
                ):
                    invalid_state_ids.append(candidate_id)
            if invalid_state_ids:
                return Response(
                    {
                        "error": "仅支持对“已完成且通过”的候选人确认入职",
                        "details": {"interview_candidate_ids": invalid_state_ids},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            now = timezone.now()
            confirmed = 0
            already_confirmed = 0
            candidate_audit_rows = []

            for candidate_id in interview_candidate_ids:
                candidate = candidate_map[candidate_id]
                is_already_confirmed = bool(candidate.is_hired)
                push_result = None
                if is_already_confirmed:
                    already_confirmed += 1
                else:
                    candidate.is_hired = True
                    candidate.hired_at = now
                    candidate.save(update_fields=["is_hired", "hired_at", "updated_at"])
                    push_result = dispatch_hire_confirmation(candidate, push_targets=push_targets)
                    confirmed += 1

                candidate_audit_rows.append(
                    {
                        "candidate": candidate,
                        "already_confirmed": is_already_confirmed,
                        "push_result": push_result,
                    }
                )

        for row in candidate_audit_rows:
            candidate = row["candidate"]
            application = candidate.application
            is_existing = row["already_confirmed"]
            summary = (
                f"确认入职（已确认）：{application.name}"
                if is_existing
                else f"确认入职：{application.name}"
            )
            self._write_operation_log(
                request,
                user=request.user,
                module="interviews",
                action="CONFIRM_HIRE",
                target_type="interview_candidate",
                target_id=candidate.id,
                target_label=application.name,
                summary=summary,
                details={
                    "interview_candidate_id": candidate.id,
                    "application_id": application.id,
                    "already_confirmed": is_existing,
                    "is_hired": candidate.is_hired,
                    "hired_at": candidate.hired_at.isoformat() if candidate.hired_at else "",
                    "push_targets": push_targets,
                    "push_result": row["push_result"] or {},
                },
                application=application,
                interview_candidate=candidate,
                region=application.region,
            )

        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="BATCH_CONFIRM_HIRE",
            target_type="interview_candidate_batch",
            target_label=f"{len(interview_candidate_ids)}名候选人",
            summary=f"批量确认入职：确认 {confirmed}，已确认 {already_confirmed}",
            details={
                "interview_candidate_ids": interview_candidate_ids,
                "confirmed": confirmed,
                "already_confirmed": already_confirmed,
                "total": len(interview_candidate_ids),
                "push_targets": push_targets,
            },
        )

        return Response(
            {
                "confirmed": confirmed,
                "already_confirmed": already_confirmed,
                "total": len(interview_candidate_ids),
            }
        )
