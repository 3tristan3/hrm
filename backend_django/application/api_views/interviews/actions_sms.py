"""面试短信相关接口。"""
from .shared import *
from .query import _InterviewCandidateAdminQuerysetMixin
from ...interview_sms import dispatch_interview_schedule_sms


class AdminInterviewCandidateResendSmsView(_InterviewCandidateAdminQuerysetMixin, APIView):
    """失败重发面试通知短信。"""

    def post(self, request: Request, pk: int):
        serializer = InterviewCandidateResendSmsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            candidate, sms_result = dispatch_interview_schedule_sms(pk, is_retry=True)
        except InterviewFlowError as err:
            return self.flow_error_response(err)

        application = candidate.application
        sms_payload = sms_result.to_payload()
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="RESEND_INTERVIEW_SMS",
            result=(
                OperationLog.RESULT_SUCCESS
                if sms_result.success
                else OperationLog.RESULT_FAILED
            ),
            target_type="interview_candidate",
            target_id=candidate.id,
            target_label=application.name,
            summary=f"重发面试短信：{application.name}",
            details={
                "interview_candidate_id": candidate.id,
                "application_id": application.id,
                "sms": sms_payload,
            },
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewCandidateListSerializer(candidate, context={"request": request})
        return Response(
            {
                "message": "短信重发成功" if sms_result.success else "短信重发失败",
                "candidate": output.data,
                "sms": sms_payload,
            }
        )
