"""面试确认入职视图子模块。"""
from .shared import *
from ...hire_push_temp import dispatch_temp_hire_push
from ...offer_status_transition import (
    OfferStatusTransitionError,
    OfferStatusTransitionService,
)


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
            invalid_offer_status_ids = []

            for candidate_id in interview_candidate_ids:
                candidate = candidate_map[candidate_id]
                try:
                    OfferStatusTransitionService.ensure_confirm_hire_eligible(candidate)
                except OfferStatusTransitionError as exc:
                    if exc.code == "invalid_candidate_state":
                        invalid_state_ids.append(candidate_id)
                    elif exc.code == "invalid_offer_status_for_confirm":
                        invalid_offer_status_ids.append(candidate_id)
            if invalid_state_ids:
                return Response(
                    {
                        "error": "仅支持对“已完成且通过”的候选人确认入职",
                        "details": {"interview_candidate_ids": invalid_state_ids},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if invalid_offer_status_ids:
                return Response(
                    {
                        "error": "仅支持对“待确认入职”状态候选人执行确认入职",
                        "details": {"interview_candidate_ids": invalid_offer_status_ids},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            now = timezone.now()
            confirmed = 0
            already_confirmed = 0
            candidate_audit_rows = []

            for candidate_id in interview_candidate_ids:
                candidate = candidate_map[candidate_id]
                OfferStatusTransitionService.apply_confirm_hire(candidate, confirmed_at=now)
                candidate.save(update_fields=["is_hired", "hired_at", "offer_status", "updated_at"])
                confirmed += 1

                candidate_audit_rows.append(
                    {
                        "candidate": candidate,
                        "already_confirmed": False,
                    }
                )

        for row in candidate_audit_rows:
            candidate = row["candidate"]
            row["oa_push"] = dispatch_temp_hire_push(candidate)

        oa_push_summary = {
            "enabled": any(bool(item.get("oa_push", {}).get("enabled")) for item in candidate_audit_rows),
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        for row in candidate_audit_rows:
            push_item = row.get("oa_push") or {}
            if not push_item.get("enabled"):
                oa_push_summary["skipped"] += 1
            elif push_item.get("success"):
                oa_push_summary["success"] += 1
            else:
                oa_push_summary["failed"] += 1

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
                    "offer_status": candidate.offer_status,
                    "oa_push": row.get("oa_push") or {},
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
                "oa_push": oa_push_summary,
            },
        )

        return Response(
            {
                "confirmed": confirmed,
                "already_confirmed": already_confirmed,
                "total": len(interview_candidate_ids),
                "oa_push": oa_push_summary,
            }
        )


class AdminPassedCandidateOfferStatusView(AdminScopedMixin, APIView):
    """更新面试通过人员的 Offer 状态。"""

    def post(self, request: Request, pk: int):
        serializer = PassedCandidateOfferStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        next_status = serializer.validated_data["offer_status"]
        region_id = self._user_region_scope()

        with transaction.atomic():
            queryset = InterviewCandidate.objects.select_for_update().select_related(
                "application",
                "application__region",
            ).filter(
                id=pk,
                status=InterviewCandidate.STATUS_COMPLETED,
                result=InterviewCandidate.RESULT_PASS,
            )
            if region_id:
                queryset = queryset.filter(application__region_id=region_id)
            candidate = get_object_or_404(queryset)

            try:
                before_status, changed = OfferStatusTransitionService.apply_offer_status_change(
                    candidate,
                    next_status,
                )
            except OfferStatusTransitionError as exc:
                return Response(
                    {
                        "error": exc.error,
                        "details": exc.details or {},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if changed:
                candidate.save(update_fields=["offer_status", "is_hired", "hired_at", "updated_at"])

        application = candidate.application
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="UPDATE_OFFER_STATUS",
            target_type="interview_candidate",
            target_id=candidate.id,
            target_label=application.name,
            summary=f"更新Offer状态：{application.name}",
            details={
                "interview_candidate_id": candidate.id,
                "application_id": application.id,
                "before_offer_status": before_status,
                "after_offer_status": candidate.offer_status,
                "is_hired": candidate.is_hired,
            },
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewPassedCandidateListSerializer(candidate, context={"request": request})
        return Response({"message": "状态已更新", "candidate": output.data})
