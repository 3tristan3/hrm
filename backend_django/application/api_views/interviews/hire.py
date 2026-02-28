"""面试通过人员 offer 发放视图子模块。"""
from .shared import *
from ...offer_status_transition import (
    OfferStatusTransitionError,
    OfferStatusTransitionService,
)
from ...oa_push import dispatch_oa_push


class AdminPassedCandidateBatchConfirmHireView(AdminScopedMixin, APIView):
    """批量发放面试通过人员 offer。"""

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
                        "error": "仅支持对“已完成且通过”的候选人发放offer",
                        "details": {"interview_candidate_ids": invalid_state_ids},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if invalid_offer_status_ids:
                return Response(
                    {
                        "error": "仅支持对“待发offer”状态候选人执行发放offer",
                        "details": {"interview_candidate_ids": invalid_offer_status_ids},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            confirmed = 0
            already_confirmed = 0
            confirmed_candidate_ids = []

            for candidate_id in interview_candidate_ids:
                candidate = candidate_map[candidate_id]
                OfferStatusTransitionService.apply_confirm_hire(candidate)
                candidate.save(update_fields=["is_hired", "hired_at", "offer_status", "updated_at"])
                confirmed += 1
                confirmed_candidate_ids.append(candidate.id)

        for candidate_id in confirmed_candidate_ids:
            candidate = candidate_map[candidate_id]
            application = candidate.application
            self._write_operation_log(
                request,
                user=request.user,
                module="interviews",
                action="CONFIRM_HIRE",
                target_type="interview_candidate",
                target_id=candidate.id,
                target_label=application.name,
                summary=f"发放offer：{application.name}",
                details={
                    "interview_candidate_id": candidate.id,
                    "application_id": application.id,
                    "already_confirmed": False,
                    "is_hired": candidate.is_hired,
                    "hired_at": candidate.hired_at.isoformat() if candidate.hired_at else "",
                    "offer_status": candidate.offer_status,
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
            summary=f"批量发放offer：发放 {confirmed}，已发 {already_confirmed}",
            details={
                "interview_candidate_ids": interview_candidate_ids,
                "confirmed": confirmed,
                "already_confirmed": already_confirmed,
                "total": len(interview_candidate_ids),
            },
        )

        return Response(
            {
                "confirmed": confirmed,
                "already_confirmed": already_confirmed,
                "total": len(interview_candidate_ids),
            }
        )


class AdminPassedCandidateBatchConfirmOnboardView(AdminScopedMixin, APIView):
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
                    OfferStatusTransitionService.ensure_confirm_onboard_eligible(candidate)
                except OfferStatusTransitionError as exc:
                    if exc.code == "invalid_candidate_state":
                        invalid_state_ids.append(candidate_id)
                    elif exc.code == "invalid_offer_status_for_onboard":
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
            confirmed_candidate_ids = []
            for candidate_id in interview_candidate_ids:
                candidate = candidate_map[candidate_id]
                OfferStatusTransitionService.apply_confirm_onboard(candidate, confirmed_at=now)
                candidate.save(update_fields=["is_hired", "hired_at", "offer_status", "updated_at"])
                confirmed += 1
                confirmed_candidate_ids.append(candidate.id)

        for candidate_id in confirmed_candidate_ids:
            candidate = candidate_map[candidate_id]
            application = candidate.application
            self._write_operation_log(
                request,
                user=request.user,
                module="interviews",
                action="CONFIRM_ONBOARD",
                target_type="interview_candidate",
                target_id=candidate.id,
                target_label=application.name,
                summary=f"确认入职：{application.name}",
                details={
                    "interview_candidate_id": candidate.id,
                    "application_id": application.id,
                    "is_hired": candidate.is_hired,
                    "hired_at": candidate.hired_at.isoformat() if candidate.hired_at else "",
                    "offer_status": candidate.offer_status,
                },
                application=application,
                interview_candidate=candidate,
                region=application.region,
            )

        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="BATCH_CONFIRM_ONBOARD",
            target_type="interview_candidate_batch",
            target_label=f"{len(interview_candidate_ids)}名候选人",
            summary=f"批量确认入职：确认 {confirmed}",
            details={
                "interview_candidate_ids": interview_candidate_ids,
                "confirmed": confirmed,
                "total": len(interview_candidate_ids),
            },
        )

        oa_push_success = 0
        oa_push_failed = 0
        oa_push_failed_items = []
        for candidate_id in confirmed_candidate_ids:
            pushed_candidate, push_result = dispatch_oa_push(candidate_id, is_retry=False)
            application = pushed_candidate.application
            if push_result.success:
                oa_push_success += 1
                self._write_operation_log(
                    request,
                    user=request.user,
                    module="interviews",
                    action="OA_PUSH_SUCCESS",
                    target_type="interview_candidate",
                    target_id=pushed_candidate.id,
                    target_label=application.name,
                    summary=f"OA推送成功：{application.name}",
                    details={
                        "interview_candidate_id": pushed_candidate.id,
                        "application_id": application.id,
                        "request_id": push_result.request_id,
                    },
                    application=application,
                    interview_candidate=pushed_candidate,
                    region=application.region,
                )
                continue

            oa_push_failed += 1
            oa_push_failed_items.append(
                {
                    "interview_candidate_id": pushed_candidate.id,
                    "application_id": application.id,
                    "error_code": push_result.error_code,
                    "error_message": push_result.error_message,
                    "retryable": push_result.retryable,
                }
            )
            self._write_operation_log(
                request,
                user=request.user,
                module="interviews",
                action="OA_PUSH_FAILED",
                target_type="interview_candidate",
                target_id=pushed_candidate.id,
                target_label=application.name,
                summary=f"OA推送失败：{application.name}",
                details={
                    "interview_candidate_id": pushed_candidate.id,
                    "application_id": application.id,
                    "error_code": push_result.error_code,
                    "error_message": push_result.error_message,
                    "retryable": push_result.retryable,
                    "oa_code": push_result.oa_code,
                    "oa_message": push_result.oa_message,
                },
                application=application,
                interview_candidate=pushed_candidate,
                region=application.region,
            )

        return Response(
            {
                "confirmed": confirmed,
                "total": len(interview_candidate_ids),
                "oa_push": {
                    "success": oa_push_success,
                    "failed": oa_push_failed,
                    "failed_items": oa_push_failed_items,
                },
            }
        )


class AdminPassedCandidateRetryOAPushView(AdminScopedMixin, APIView):
    """重发单个候选人的 OA 推送。"""

    def post(self, request: Request, pk: int):
        serializer = PassedCandidateRetryOAPushSerializer(data=request.data or {})
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        region_id = self._user_region_scope()
        queryset = InterviewCandidate.objects.select_related(
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

        pushed_candidate, push_result = dispatch_oa_push(candidate.id, is_retry=True)
        application = pushed_candidate.application
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="OA_PUSH_RETRY",
            target_type="interview_candidate",
            target_id=pushed_candidate.id,
            target_label=application.name,
            summary=f"重发OA推送：{application.name}",
            details={
                "interview_candidate_id": pushed_candidate.id,
                "application_id": application.id,
                "success": push_result.success,
                "retryable": push_result.retryable,
                "request_id": push_result.request_id,
                "error_code": push_result.error_code,
                "error_message": push_result.error_message,
                "oa_code": push_result.oa_code,
                "oa_message": push_result.oa_message,
            },
            application=application,
            interview_candidate=pushed_candidate,
            region=application.region,
            result=OperationLog.RESULT_SUCCESS if push_result.success else OperationLog.RESULT_FAILED,
        )
        output = InterviewPassedCandidateListSerializer(pushed_candidate, context={"request": request})
        return Response(
            {
                "message": "重发完成" if push_result.success else "重发失败",
                "oa_push": push_result.to_payload(),
                "candidate": output.data,
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
