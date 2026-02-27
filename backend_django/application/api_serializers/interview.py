"""按职责拆分的序列化器模块。"""
from .shared import *

class InterviewCandidateBatchAddSerializer(serializers.Serializer):
    """批量加入拟面试人员入参。"""

    application_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )

    def validate_application_ids(self, value):
        unique_ids = list(dict.fromkeys(value))
        if len(unique_ids) > 200:
            raise serializers.ValidationError("单次最多选择 200 条应聘记录")
        return unique_ids

class InterviewCandidateBatchRemoveSerializer(serializers.Serializer):
    """批量移出拟面试人员入参。"""

    interview_candidate_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )

    def validate_interview_candidate_ids(self, value):
        unique_ids = list(dict.fromkeys(value))
        if len(unique_ids) > 200:
            raise serializers.ValidationError("单次最多选择 200 条拟面试人员")
        return unique_ids

class InterviewCandidateBatchConfirmHireSerializer(serializers.Serializer):
    """批量确认入职入参。"""

    interview_candidate_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )

    def validate_interview_candidate_ids(self, value):
        unique_ids = list(dict.fromkeys(value))
        if len(unique_ids) > 200:
            raise serializers.ValidationError("单次最多选择 200 条面试通过人员")
        return unique_ids

class InterviewCandidateListSerializer(serializers.ModelSerializer):
    """拟面试人员列表输出，包含应聘主信息和当前面试状态。"""

    application_id = serializers.IntegerField(source="application.id", read_only=True)
    name = serializers.CharField(source="application.name", read_only=True)
    phone = serializers.CharField(source="application.phone", read_only=True)
    recruit_type = serializers.CharField(source="application.recruit_type", read_only=True)
    education_level = serializers.CharField(source="application.education_level", read_only=True)
    region_name = serializers.CharField(source="application.region.name", read_only=True)
    job_title = serializers.CharField(source="application.job.title", read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = InterviewCandidate
        fields = [
            "id",
            "application_id",
            "name",
            "phone",
            "recruit_type",
            "education_level",
            "region_name",
            "job_title",
            "status",
            "interview_round",
            "interview_at",
            "interviewer",
            "interviewers",
            "interview_location",
            "result",
            "score",
            "interviewer_scores",
            "result_note",
            "result_at",
            "offer_status",
            "note",
            "sms_status",
            "sms_retry_count",
            "sms_last_attempt_at",
            "sms_sent_at",
            "sms_updated_at",
            "sms_error",
            "sms_provider_code",
            "sms_provider_message",
            "sms_message_id",
            "photo_url",
            "created_at",
            "updated_at",
        ]

    def get_photo_url(self, obj):
        application = obj.application
        attachments = getattr(application, "photo_attachments", None)
        attachment = None
        if isinstance(attachments, list):
            attachment = attachments[0] if attachments else None
        else:
            attachment = (
                application.attachments.filter(category="photo")
                .order_by("-created_at")
                .first()
            )
        if not attachment or not attachment.file:
            return ""
        request = self.context.get("request")
        return build_public_file_url(attachment.file, request=request)

class InterviewPassedCandidateListSerializer(serializers.ModelSerializer):
    """面试通过人员列表输出，聚合一到三轮快照字段。"""

    application_id = serializers.IntegerField(source="application.id", read_only=True)
    name = serializers.CharField(source="application.name", read_only=True)
    phone = serializers.CharField(source="application.phone", read_only=True)
    recruit_type = serializers.CharField(source="application.recruit_type", read_only=True)
    education_level = serializers.CharField(source="application.education_level", read_only=True)
    region_name = serializers.CharField(source="application.region.name", read_only=True)
    job_title = serializers.CharField(source="application.job.title", read_only=True)
    is_hired = serializers.BooleanField(read_only=True)
    hired_at = serializers.DateTimeField(read_only=True)
    first_round_at = serializers.SerializerMethodField()
    first_round_score = serializers.SerializerMethodField()
    first_round_interviewer = serializers.SerializerMethodField()
    first_round_interviewer_scores = serializers.SerializerMethodField()
    second_round_at = serializers.SerializerMethodField()
    second_round_score = serializers.SerializerMethodField()
    second_round_interviewer = serializers.SerializerMethodField()
    second_round_interviewer_scores = serializers.SerializerMethodField()
    third_round_at = serializers.SerializerMethodField()
    third_round_score = serializers.SerializerMethodField()
    third_round_interviewer = serializers.SerializerMethodField()
    third_round_interviewer_scores = serializers.SerializerMethodField()

    class Meta:
        model = InterviewCandidate
        fields = [
            "id",
            "application_id",
            "status",
            "result",
            "interview_round",
            "name",
            "job_title",
            "region_name",
            "phone",
            "recruit_type",
            "education_level",
            "is_hired",
            "hired_at",
            "offer_status",
            "first_round_at",
            "first_round_score",
            "first_round_interviewer",
            "first_round_interviewer_scores",
            "second_round_at",
            "second_round_score",
            "second_round_interviewer",
            "second_round_interviewer_scores",
            "third_round_at",
            "third_round_score",
            "third_round_interviewer",
            "third_round_interviewer_scores",
        ]

    def _round_record_map(self, obj):
        """构建轮次到记录的映射并缓存，避免重复遍历。"""
        cached = getattr(obj, "_cached_round_record_map", None)
        if cached is not None:
            return cached
        records = list(getattr(obj, "round_records").all())
        record_map = {}
        for record in records:
            if record.round_no not in record_map:
                record_map[record.round_no] = record
        setattr(obj, "_cached_round_record_map", record_map)
        return record_map

    def _round_record(self, obj, round_no):
        return self._round_record_map(obj).get(round_no)

    def _round_interview_at(self, obj, round_no):
        record = self._round_record(obj, round_no)
        return record.interview_at if record else None

    def _round_score(self, obj, round_no):
        record = self._round_record(obj, round_no)
        return record.score if record else None

    def _round_interviewer(self, obj, round_no):
        record = self._round_record(obj, round_no)
        return record.interviewer if record else ""

    def _round_interviewer_scores(self, obj, round_no):
        record = self._round_record(obj, round_no)
        if not record:
            return []
        return record.interviewer_scores or []

    def get_first_round_at(self, obj):
        return self._round_interview_at(obj, 1)

    def get_first_round_score(self, obj):
        return self._round_score(obj, 1)

    def get_first_round_interviewer(self, obj):
        return self._round_interviewer(obj, 1)

    def get_first_round_interviewer_scores(self, obj):
        return self._round_interviewer_scores(obj, 1)

    def get_second_round_at(self, obj):
        return self._round_interview_at(obj, 2)

    def get_second_round_score(self, obj):
        return self._round_score(obj, 2)

    def get_second_round_interviewer(self, obj):
        return self._round_interviewer(obj, 2)

    def get_second_round_interviewer_scores(self, obj):
        return self._round_interviewer_scores(obj, 2)

    def get_third_round_at(self, obj):
        return self._round_interview_at(obj, 3)

    def get_third_round_score(self, obj):
        return self._round_score(obj, 3)

    def get_third_round_interviewer(self, obj):
        return self._round_interviewer(obj, 3)

    def get_third_round_interviewer_scores(self, obj):
        return self._round_interviewer_scores(obj, 3)

class InterviewCandidateScheduleSerializer(serializers.Serializer):
    """安排/改期面试入参。"""

    interview_at = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M", "iso-8601"])
    interviewer = serializers.CharField(max_length=100, required=False, allow_blank=True)
    interviewers = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
    )
    interview_location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    send_sms = serializers.BooleanField(required=False, default=False)

    def validate_interview_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("面试时间不能早于当前时间")
        return value

    def validate_interviewers(self, value):
        names = []
        seen = set()
        for raw in value or []:
            name = str(raw or "").strip()
            if not name:
                continue
            if name in seen:
                continue
            seen.add(name)
            names.append(name)
        if len(names) > 10:
            raise serializers.ValidationError("单场面试最多填写 10 位面试官")
        return names

    def validate(self, attrs):
        interviewers = attrs.get("interviewers", None)
        interviewer = str(attrs.get("interviewer", "") or "").strip()
        if not interviewers and interviewer:
            raw = interviewer
            for separator in ("、", "，", ";", "；", "/", "|"):
                raw = raw.replace(separator, ",")
            attrs["interviewers"] = self.validate_interviewers(raw.split(","))
        if interviewers and not interviewer:
            attrs["interviewer"] = "、".join(interviewers)
        return attrs

class InterviewCandidateCancelScheduleSerializer(serializers.Serializer):
    """取消安排入参。"""

    note = serializers.CharField(required=False, allow_blank=True)

class InterviewCandidateResultSerializer(serializers.Serializer):
    """面试结果录入入参。"""

    result = serializers.ChoiceField(choices=InterviewCandidate.RESULT_CHOICES)
    score = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    interviewer_scores = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )
    result_note = serializers.CharField(required=False, allow_blank=True)

    def validate_interviewer_scores(self, value):
        rows = []
        seen = set()
        for item in value or []:
            if not isinstance(item, dict):
                raise serializers.ValidationError("面试官评分项格式不正确")
            interviewer = str(item.get("interviewer") or "").strip()
            score = item.get("score", None)
            if not interviewer:
                raise serializers.ValidationError("面试官姓名不能为空")
            if interviewer in seen:
                raise serializers.ValidationError("面试官姓名不能重复")
            try:
                score_value = int(score)
            except (TypeError, ValueError):
                raise serializers.ValidationError("面试官评分必须是 0-100 的整数")
            if score_value < 0 or score_value > 100:
                raise serializers.ValidationError("面试官评分必须是 0-100 的整数")
            seen.add(interviewer)
            rows.append({"interviewer": interviewer, "score": score_value})
        if len(rows) > 10:
            raise serializers.ValidationError("单场面试最多记录 10 位面试官评分")
        return rows


class PassedCandidateOfferStatusSerializer(serializers.Serializer):
    """通过人员状态更新入参。"""

    offer_status = serializers.ChoiceField(
        choices=[
            InterviewCandidate.OFFER_STATUS_PENDING,
            InterviewCandidate.OFFER_STATUS_REJECTED,
        ]
    )


class InterviewCandidateResendSmsSerializer(serializers.Serializer):
    """失败重发短信入参。"""
