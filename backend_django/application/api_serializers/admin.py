"""按职责拆分的序列化器模块。"""
from .shared import *

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
