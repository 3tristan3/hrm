"""面试域视图子模块。"""
from .shared import *
from .query import _InterviewCandidateAdminQuerysetMixin

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
                    interview_location=data.get("interview_location", ""),
                    note=data.get("note", None),
                )
        except InterviewFlowError as err:
            return self.flow_error_response(err)

        action = "RESCHEDULE_INTERVIEW" if was_scheduled else "SCHEDULE_INTERVIEW"
        application = candidate.application
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
                "interview_location": candidate.interview_location,
            },
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewCandidateListSerializer(candidate, context={"request": request})
        return Response({"message": "面试安排已保存", "candidate": output.data})

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
        score = data.get("score", None)
        result_note = data.get("result_note", "")

        try:
            with transaction.atomic():
                candidate = self.get_locked_candidate(pk)
                record_result(
                    candidate,
                    result=result,
                    score=score,
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
                "result": candidate.result,
                "score": candidate.score,
            },
            application=application,
            interview_candidate=candidate,
            region=application.region,
        )
        output = InterviewCandidateListSerializer(candidate, context={"request": request})
        return Response({"message": "面试结果已保存", "candidate": output.data})
