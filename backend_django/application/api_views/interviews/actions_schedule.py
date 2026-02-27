"""面试安排相关接口。"""
from .shared import *
from .query import _InterviewCandidateAdminQuerysetMixin
from ...interview_sms import SmsDispatchResult, dispatch_interview_schedule_sms


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
        should_send_sms = bool(data.get("send_sms", False))
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
                    interviewers=data.get("interviewers", None),
                    interview_location=data.get("interview_location", ""),
                    note=data.get("note", None),
                )
                if not should_send_sms:
                    candidate.sms_status = InterviewCandidate.SMS_STATUS_IDLE
                    candidate.sms_retry_count = 0
                    candidate.sms_last_attempt_at = None
                    candidate.sms_sent_at = None
                    candidate.sms_updated_at = timezone.now()
                    candidate.sms_error = ""
                    candidate.sms_provider_code = ""
                    candidate.sms_provider_message = ""
                    candidate.sms_message_id = ""
                    candidate.save(
                        update_fields=[
                            "sms_status",
                            "sms_retry_count",
                            "sms_last_attempt_at",
                            "sms_sent_at",
                            "sms_updated_at",
                            "sms_error",
                            "sms_provider_code",
                            "sms_provider_message",
                            "sms_message_id",
                            "updated_at",
                        ]
                    )
        except InterviewFlowError as err:
            return self.flow_error_response(err)

        sms_result = None
        if should_send_sms:
            try:
                candidate, sms_result = dispatch_interview_schedule_sms(candidate.id, is_retry=False)
            except InterviewFlowError as err:
                candidate = (
                    InterviewCandidate.objects.select_related("application", "application__region", "application__job")
                    .get(pk=candidate.id)
                )
                sms_result = SmsDispatchResult(
                    success=False,
                    provider_code=err.code,
                    provider_message=err.message,
                )

        action = "RESCHEDULE_INTERVIEW" if was_scheduled else "SCHEDULE_INTERVIEW"
        application = candidate.application
        sms_payload = sms_result.to_payload() if sms_result else {}
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
                "interviewers": candidate.interviewers,
                "interview_location": candidate.interview_location,
                "send_sms": should_send_sms,
                "sms": sms_payload,
            },
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewCandidateListSerializer(candidate, context={"request": request})
        message = "面试安排已保存"
        if should_send_sms:
            message = "面试安排已保存，短信已发送" if sms_result and sms_result.success else "面试安排已保存，短信发送失败"
        return Response(
            {
                "message": message,
                "candidate": output.data,
                "sms": sms_payload,
            }
        )


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
