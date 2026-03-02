"""面试结果相关接口。"""
from .shared import *
from .query import _InterviewCandidateAdminQuerysetMixin


class AdminInterviewCandidateResultView(_InterviewCandidateAdminQuerysetMixin, APIView):
    """记录面试结果并推进到下一状态。"""

    def post(self, request: Request, pk: int):
        serializer = InterviewCandidateResultSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        result = data["result"]
        interviewer_decisions = data["interviewer_decisions"]
        result_note = data.get("result_note", "")

        try:
            with transaction.atomic():
                candidate = self.get_locked_candidate(pk)
                record_result(
                    candidate,
                    result=result,
                    interviewer_decisions=interviewer_decisions,
                    result_note=result_note,
                )
        except InterviewFlowError as err:
            return self.flow_error_response(err)

        application = candidate.application
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="SAVE_INTERVIEW_RESULT",
            target_type="interview_candidate",
            target_id=candidate.id,
            target_label=application.name,
            summary=f"记录面试结果：{application.name}",
            details={
                "interview_candidate_id": candidate.id,
                "application_id": application.id,
                "round": candidate.interview_round,
                "interviewer_decisions": interviewer_decisions,
                "result": candidate.result,
                "score": candidate.score,
                "interviewer_scores": candidate.interviewer_scores,
            },
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewCandidateListSerializer(candidate, context={"request": request})
        return Response({"message": "面试结果已保存", "candidate": output.data})
