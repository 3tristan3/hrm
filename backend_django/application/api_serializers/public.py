"""按职责拆分的序列化器模块。"""
from .shared import *

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
            job = Job.objects.get(id=attrs["job_id"], is_active=True, is_deleted=False)
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
