"""DRF 序列化器定义，负责接口参数校验与响应结构组装。"""
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import (
    Application,
    ApplicationAttachment,
    InterviewCandidate,
    Job,
    Region,
    RegionField,
    UserProfile,
)


def build_public_file_url(file_field, request=None):
    if not file_field:
        return ""
    url = str(file_field.url or "")
    if not url:
        return ""
    if not url.startswith("/"):
        url = f"/{url}"
    media_base = getattr(settings, "MEDIA_BASE_URL", "")
    if media_base:
        return f"{media_base}{url}"
    return url


class RegionFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionField
        fields = ["id", "key", "label", "field_type", "required", "options"]


class RegionSerializer(serializers.ModelSerializer):
    region_fields = RegionFieldSerializer(many=True, read_only=True, source="fields")

    class Meta:
        model = Region
        fields = ["id", "name", "code", "region_fields"]


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["id", "title", "description", "salary", "education", "region_id"]


class ApplicationCreateSerializer(serializers.Serializer):
    region_id = serializers.IntegerField()
    job_id = serializers.IntegerField()
    recruit_type = serializers.ChoiceField(choices=["社招", "校招"])
    apply_region = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(max_length=50)
    age = serializers.IntegerField()
    gender = serializers.ChoiceField(choices=["男", "女"])
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    apply_company = serializers.CharField(required=False, allow_blank=True)
    available_date = serializers.DateField(
        required=False, allow_null=True, input_formats=["%Y-%m-%d"]
    )
    expected_salary = serializers.CharField(required=False, allow_blank=True)
    recruitment_source = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=[
            "招聘网站",
            "贵公司人员介绍",
            "行政单位人员介绍",
            "其他",
            "公司内岗位调整",
        ],
    )
    referrer_name = serializers.CharField(required=False, allow_blank=True)
    referrer_relation = serializers.CharField(required=False, allow_blank=True)
    referrer_company = serializers.CharField(required=False, allow_blank=True)
    marital_status = serializers.ChoiceField(
        choices=["未婚", "已婚", "离异", "丧偶"]
    )
    birth_month = serializers.DateField(
        required=False, allow_null=True, input_formats=["%Y-%m"]
    )
    height_cm = serializers.IntegerField()
    weight_kg = serializers.IntegerField()
    health_status = serializers.CharField(required=False, allow_blank=True)
    graduate_school = serializers.CharField(required=False, allow_blank=True)
    graduation_date = serializers.DateField(
        required=False, allow_null=True, input_formats=["%Y-%m"]
    )
    major = serializers.CharField(required=False, allow_blank=True)
    title_cert = serializers.CharField(required=False, allow_blank=True)
    education_level = serializers.ChoiceField(
        choices=[
            "初中",
            "高中",
            "中专",
            "大专",
            "本科",
            "985/211本科",
            "硕士",
            "985/211硕士",
            "博士",
        ]
    )
    education_period = serializers.CharField()
    diploma_number = serializers.CharField(required=False, allow_blank=True)
    political_status = serializers.CharField()
    ethnicity = serializers.CharField()
    hukou_type = serializers.CharField(required=False, allow_blank=True)
    native_place = serializers.CharField(required=False, allow_blank=True)
    hukou_address = serializers.CharField(required=False, allow_blank=True)
    current_address = serializers.CharField(required=False, allow_blank=True)
    id_number = serializers.CharField()
    qq = serializers.CharField(max_length=30)
    wechat = serializers.CharField(max_length=50)
    emergency_name = serializers.CharField(required=False, allow_blank=True)
    emergency_phone = serializers.CharField(required=False, allow_blank=True)
    hobbies = serializers.CharField(required=False, allow_blank=True)
    self_evaluation = serializers.CharField(required=False, allow_blank=True)
    education_history = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    work_history = serializers.ListField(child=serializers.DictField(), required=False)
    family_members = serializers.ListField(child=serializers.DictField(), required=False)
    extra_fields = serializers.DictField(required=False)

    def validate_phone(self, value):
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        if len(digits) != 11:
            raise serializers.ValidationError("手机号格式不正确")
        return value

    def validate_id_number(self, value):
        cleaned = value.strip()
        if len(cleaned) != 18:
            raise serializers.ValidationError("身份证号需为18位")
        return cleaned

    def validate_age(self, value):
        if value <= 0:
            raise serializers.ValidationError("年龄需大于0")
        return value

    def validate_height_cm(self, value):
        if value <= 0:
            raise serializers.ValidationError("身高需大于0")
        return value

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("体重需大于0")
        return value

    def validate_education_period(self, value):
        if "-" not in value:
            raise serializers.ValidationError("最高学历起止时间格式不正确")
        return value

    def validate(self, attrs):
        try:
            region = Region.objects.get(id=attrs["region_id"], is_active=True)
        except Region.DoesNotExist:
            raise serializers.ValidationError({"region_id": "地区不存在"})

        try:
            job = Job.objects.get(id=attrs["job_id"], is_active=True)
        except Job.DoesNotExist:
            raise serializers.ValidationError({"job_id": "岗位不存在"})

        job_region_id = getattr(job, "region_id", None)
        region_pk = getattr(region, "pk", None)
        if job_region_id != region_pk:
            raise serializers.ValidationError({"job_id": "岗位与地区不匹配"})

        extra_fields = attrs.get("extra_fields") or {}
        required_fields = region.fields.filter(required=True)
        extra_errors = {}
        for field in required_fields:
            value = extra_fields.get(field.key)
            if value is None or (isinstance(value, str) and not value.strip()) or value == "":
                extra_errors[field.key] = f"{field.label}为必填"
        if extra_errors:
            raise serializers.ValidationError(extra_errors)

        def is_row_complete(row, fields):
            for field in fields:
                value = row.get(field)
                if field == "age":
                    try:
                        if value is None or int(value) <= 0:
                            return False
                    except (TypeError, ValueError):
                        return False
                else:
                    if value is None or (isinstance(value, str) and not value.strip()):
                        return False
            return True

        education_history = attrs.get("education_history") or []
        if len(education_history) < 1:
            raise serializers.ValidationError({"education_history": "请至少填写一条教育/培训经历"})
        if not all(
            is_row_complete(row, ["school", "major", "degree", "start", "end"])
            for row in education_history
        ):
            raise serializers.ValidationError({"education_history": "教育/培训经历每一条内容均为必填"})

        family_members = attrs.get("family_members") or []
        if len(family_members) < 2:
            raise serializers.ValidationError({"family_members": "请至少填写两位家庭成员"})
        if not all(
            is_row_complete(row, ["name", "relation", "age", "company", "position", "phone"])
            for row in family_members
        ):
            raise serializers.ValidationError({"family_members": "家庭成员信息每一条内容均为必填"})

        work_history = attrs.get("work_history") or []
        if len(work_history) < 1:
            raise serializers.ValidationError({"work_history": "请至少填写一条工作经历"})
        if not all(
            is_row_complete(row, ["company", "position", "start", "end"])
            for row in work_history
        ):
            raise serializers.ValidationError({"work_history": "工作经历每一条内容均为必填"})

        attrs["region"] = region
        attrs["job"] = job
        return attrs


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            "id",
            "name",
            "recruit_type",
            "apply_region",
            "age",
            "gender",
            "phone",
            "email",
            "region_id",
            "job_id",
            "apply_company",
            "available_date",
            "expected_salary",
            "recruitment_source",
            "referrer_name",
            "referrer_relation",
            "referrer_company",
            "marital_status",
            "birth_month",
            "height_cm",
            "weight_kg",
            "health_status",
            "graduate_school",
            "graduation_date",
            "major",
            "title_cert",
            "education_level",
            "education_period",
            "diploma_number",
            "political_status",
            "ethnicity",
            "hukou_type",
            "native_place",
            "hukou_address",
            "current_address",
            "id_number",
            "qq",
            "wechat",
            "emergency_name",
            "emergency_phone",
            "hobbies",
            "self_evaluation",
            "education_history",
            "work_history",
            "family_members",
            "extra_fields",
            "created_at",
        ]


class RegionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name", "code", "is_active", "order"]


class RegionFieldAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionField
        fields = [
            "id",
            "region",
            "key",
            "label",
            "field_type",
            "required",
            "options",
            "order",
        ]


class JobAdminSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source="region.name", read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "region",
            "region_name",
            "title",
            "description",
            "salary",
            "education",
            "is_active",
            "order",
        ]


class JobBatchStatusSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
    is_active = serializers.BooleanField()

    def validate_job_ids(self, value):
        unique_ids = list(dict.fromkeys(value))
        if len(unique_ids) > 200:
            raise serializers.ValidationError("单次最多选择 200 个岗位")
        return unique_ids


class ApplicationAdminPhotoMixin(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    def _file_url(self, file_field):
        request = self.context.get("request")
        return build_public_file_url(file_field, request=request)

    def get_photo_url(self, obj):
        attachments = getattr(obj, "photo_attachments", None)
        attachment = None
        if isinstance(attachments, list):
            attachment = attachments[0] if attachments else None
        else:
            attachment = obj.attachments.filter(category="photo").order_by("-created_at").first()
        if not attachment or not attachment.file:
            return ""
        return self._file_url(attachment.file)


class ApplicationAdminListSerializer(ApplicationAdminPhotoMixin):
    region_name = serializers.CharField(source="region.name", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "name",
            "gender",
            "age",
            "phone",
            "recruit_type",
            "education_level",
            "region_name",
            "job_title",
            "photo_url",
            "created_at",
        ]


class ApplicationAdminSerializer(ApplicationAdminPhotoMixin):
    region_name = serializers.CharField(source="region.name", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "name",
            "recruit_type",
            "apply_region",
            "age",
            "gender",
            "phone",
            "email",
            "education_period",
            "apply_company",
            "available_date",
            "expected_salary",
            "recruitment_source",
            "referrer_name",
            "referrer_relation",
            "referrer_company",
            "marital_status",
            "birth_month",
            "height_cm",
            "weight_kg",
            "health_status",
            "graduate_school",
            "graduation_date",
            "major",
            "title_cert",
            "education_level",
            "diploma_number",
            "political_status",
            "ethnicity",
            "hukou_type",
            "native_place",
            "hukou_address",
            "current_address",
            "id_number",
            "qq",
            "wechat",
            "emergency_name",
            "emergency_phone",
            "hobbies",
            "self_evaluation",
            "education_history",
            "work_history",
            "family_members",
            "region_name",
            "job_title",
            "photo_url",
            "created_at",
            "extra_fields",
            "attachments",
        ]

    def get_attachments(self, obj):
        attachments = obj.attachments.all().order_by("-created_at", "-id")
        return [
            {
                "id": attachment.id,
                "category": attachment.category,
                "category_label": attachment.get_category_display(),
                "file_url": self._file_url(attachment.file),
                "file_name": str(attachment.file.name or "").split("/")[-1],
                "created_at": attachment.created_at,
            }
            for attachment in attachments
            if attachment.file
        ]


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
            "interview_location",
            "result",
            "score",
            "result_note",
            "result_at",
            "note",
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

    name = serializers.CharField(source="application.name", read_only=True)
    phone = serializers.CharField(source="application.phone", read_only=True)
    recruit_type = serializers.CharField(source="application.recruit_type", read_only=True)
    education_level = serializers.CharField(source="application.education_level", read_only=True)
    region_name = serializers.CharField(source="application.region.name", read_only=True)
    job_title = serializers.CharField(source="application.job.title", read_only=True)
    first_round_at = serializers.SerializerMethodField()
    first_round_score = serializers.SerializerMethodField()
    first_round_interviewer = serializers.SerializerMethodField()
    second_round_at = serializers.SerializerMethodField()
    second_round_score = serializers.SerializerMethodField()
    second_round_interviewer = serializers.SerializerMethodField()
    third_round_at = serializers.SerializerMethodField()
    third_round_score = serializers.SerializerMethodField()
    third_round_interviewer = serializers.SerializerMethodField()

    class Meta:
        model = InterviewCandidate
        fields = [
            "id",
            "name",
            "job_title",
            "region_name",
            "phone",
            "recruit_type",
            "education_level",
            "first_round_at",
            "first_round_score",
            "first_round_interviewer",
            "second_round_at",
            "second_round_score",
            "second_round_interviewer",
            "third_round_at",
            "third_round_score",
            "third_round_interviewer",
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

    def get_first_round_at(self, obj):
        return self._round_interview_at(obj, 1)

    def get_first_round_score(self, obj):
        return self._round_score(obj, 1)

    def get_first_round_interviewer(self, obj):
        return self._round_interviewer(obj, 1)

    def get_second_round_at(self, obj):
        return self._round_interview_at(obj, 2)

    def get_second_round_score(self, obj):
        return self._round_score(obj, 2)

    def get_second_round_interviewer(self, obj):
        return self._round_interviewer(obj, 2)

    def get_third_round_at(self, obj):
        return self._round_interview_at(obj, 3)

    def get_third_round_score(self, obj):
        return self._round_score(obj, 3)

    def get_third_round_interviewer(self, obj):
        return self._round_interviewer(obj, 3)


class ApplicationAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationAttachment
        fields = ["id", "category", "file", "file_url", "created_at"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        return build_public_file_url(obj.file, request=request)


class ApplicationAttachmentUploadSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=ApplicationAttachment.CATEGORY_CHOICES)
    file = serializers.FileField()


class InterviewCandidateScheduleSerializer(serializers.Serializer):
    """安排/改期面试入参。"""

    interview_at = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M", "iso-8601"])
    interviewer = serializers.CharField(max_length=100, required=False, allow_blank=True)
    interview_location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate_interview_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("面试时间不能早于当前时间")
        return value


class InterviewCandidateCancelScheduleSerializer(serializers.Serializer):
    """取消安排入参。"""

    note = serializers.CharField(required=False, allow_blank=True)


class InterviewCandidateResultSerializer(serializers.Serializer):
    """面试结果录入入参。"""

    result = serializers.ChoiceField(choices=InterviewCandidate.RESULT_CHOICES)
    score = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    result_note = serializers.CharField(required=False, allow_blank=True)


User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    region_id = serializers.IntegerField()

    def validate_region_id(self, value):
        if not Region.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("地区不存在")
        return value

    def create(self, validated_data):
        username = validated_data["username"]
        password = validated_data["password"]
        region = Region.objects.get(id=validated_data["region_id"])

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "账号已存在"})

        user = User.objects.create_user(username=username, password=password)
        can_view_all = False
        UserProfile.objects.create(user=user, region=region, can_view_all=can_view_all)
        token, _ = Token.objects.get_or_create(user=user)
        return {"token": token.key, "user": user, "region": region, "can_view_all": can_view_all}


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("账号或密码错误")
        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source="region.name", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["region", "region_name", "can_view_all"]


class MeSerializer(serializers.Serializer):
    username = serializers.CharField()
    is_superuser = serializers.BooleanField()
    profile = UserProfileSerializer()


class AdminUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    is_superuser = serializers.BooleanField()
    is_active = serializers.BooleanField()
    region_id = serializers.SerializerMethodField()
    region_name = serializers.SerializerMethodField()

    def get_region_id(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.region_id if profile else None

    def get_region_name(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and profile.region_id:
            return getattr(profile.region, "name", "")
        return ""


class AdminPasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=128)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6, max_length=128)
