"""面试域视图子模块。"""
from .shared import *

class _InterviewCandidateAdminQuerysetMixin(AdminScopedMixin):
    """拟面试人员模块共用能力：查询范围、行锁读取、流程错误输出。"""

    def get_queryset(self):
        """返回带应聘信息的候选人列表，并按账号地区做数据隔离。"""
        queryset = InterviewCandidate.objects.select_related(
            "application",
            "application__region",
            "application__job",
        ).prefetch_related(
            Prefetch(
                "application__attachments",
                queryset=ApplicationAttachment.objects.filter(category="photo").order_by(
                    "-created_at"
                ),
                to_attr="photo_attachments",
            )
        )
        region_id = self._user_region_scope()
        if region_id:
            queryset = queryset.filter(application__region_id=region_id)
        return queryset

    def get_locked_candidate(self, pk: int) -> InterviewCandidate:
        """在事务中读取并锁定候选人，避免并发写导致状态错乱。"""
        queryset = InterviewCandidate.objects.select_for_update().select_related(
            "application",
            "application__region",
            "application__job",
        )
        region_id = self._user_region_scope()
        if region_id:
            queryset = queryset.filter(application__region_id=region_id)
        return get_object_or_404(queryset, pk=pk)

    @staticmethod
    def flow_error_response(error: InterviewFlowError) -> Response:
        """统一输出流程层业务错误。"""
        return Response(error.to_payload(), status=error.status_code)

class AdminInterviewCandidateListView(_InterviewCandidateAdminQuerysetMixin, generics.ListAPIView):
    serializer_class = InterviewCandidateListSerializer

    def get_queryset(self):
        # 拟面试池仅展示流程中的候选人，已出结果（已完成）移出该列表。
        return super().get_queryset().exclude(status=InterviewCandidate.STATUS_COMPLETED)

class AdminInterviewMetaView(AdminScopedMixin, APIView):
    """输出面试模块元数据，供前端统一常量和选项。"""

    def get(self, request: Request):
        return Response(
            {
                "status_pending": InterviewCandidate.STATUS_PENDING,
                "status_scheduled": InterviewCandidate.STATUS_SCHEDULED,
                "status_completed": InterviewCandidate.STATUS_COMPLETED,
                "result_pending": InterviewCandidate.RESULT_PENDING,
                "result_next_round": InterviewCandidate.RESULT_NEXT_ROUND,
                "result_pass": InterviewCandidate.RESULT_PASS,
                "result_reject": InterviewCandidate.RESULT_REJECT,
                "status_choices": [
                    {"value": value, "label": label}
                    for value, label in InterviewCandidate.STATUS_CHOICES
                ],
                "result_choices": [
                    {"value": value, "label": label}
                    for value, label in InterviewCandidate.RESULT_CHOICES
                ],
                "final_results": list(FINAL_RESULTS),
                "max_round": MAX_INTERVIEW_ROUND,
            }
        )

class _InterviewOutcomeCandidateListView(_InterviewCandidateAdminQuerysetMixin, generics.ListAPIView):
    """面试结果池列表基类：按最终结果筛选并输出轮次快照。"""

    serializer_class = InterviewPassedCandidateListSerializer
    pagination_class = AdminResultListPagination
    outcome_result: str = ""

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            status=InterviewCandidate.STATUS_COMPLETED,
            result=self.outcome_result,
        )
        return queryset.prefetch_related(
            Prefetch(
                "round_records",
                queryset=InterviewRoundRecord.objects.order_by("round_no", "id"),
            )
        ).order_by("-result_at", "-updated_at", "-id")

    def list(self, request: Request, *args, **kwargs):
        """兼容历史返回：仅当前端传 page/page_size 时启用分页结构。"""
        if "page" not in request.query_params and "page_size" not in request.query_params:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

class AdminPassedCandidateListView(_InterviewOutcomeCandidateListView):
    """面试通过人员列表，含各轮次快照信息。"""

    outcome_result = InterviewCandidate.RESULT_PASS

class AdminTalentPoolCandidateListView(_InterviewOutcomeCandidateListView):
    """人才库列表（面试淘汰人员），含各轮次快照信息。"""

    outcome_result = InterviewCandidate.RESULT_REJECT

class AdminInterviewCandidateDetailView(
    _InterviewCandidateAdminQuerysetMixin, generics.DestroyAPIView
):
    serializer_class = InterviewCandidateListSerializer

    def destroy(self, request: Request, *args, **kwargs):
        candidate = self.get_object()
        application = candidate.application
        candidate_id = candidate.id
        response = super().destroy(request, *args, **kwargs)
        self._write_operation_log(
            request,
            user=request.user,
            module="interviews",
            action="REMOVE_FROM_INTERVIEW_POOL",
            target_type="interview_candidate",
            target_id=candidate_id,
            target_label=application.name,
            summary=f"移出拟面试人员：{application.name}",
            details={"interview_candidate_id": candidate_id, "application_id": application.id},
            application=application,
            region=application.region,
        )
        return response
