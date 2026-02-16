"""按职责拆分的序列化器模块。"""
from .shared import *

class OperationLogListSerializer(serializers.ModelSerializer):
    """操作日志列表输出。"""

    operator_id = serializers.IntegerField(source="operator.id", read_only=True, allow_null=True)
    application_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = OperationLog
        fields = [
            "id",
            "created_at",
            "module",
            "action",
            "result",
            "summary",
            "target_type",
            "target_id",
            "target_label",
            "application_id",
            "operator_id",
            "operator_username",
            "operator_role",
            "operator_region_name",
            "request_id",
        ]

class OperationLogDetailSerializer(serializers.ModelSerializer):
    """操作日志详情输出（按需加载 details）。"""

    operator_id = serializers.IntegerField(source="operator.id", read_only=True, allow_null=True)
    application_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = OperationLog
        fields = [
            "id",
            "created_at",
            "module",
            "action",
            "result",
            "summary",
            "target_type",
            "target_id",
            "target_label",
            "application_id",
            "operator_id",
            "operator_username",
            "operator_role",
            "operator_region_name",
            "details",
            "request_id",
        ]

class OperationLogQuerySerializer(serializers.Serializer):
    """操作日志列表查询参数校验与规范化。"""

    application_id = serializers.IntegerField(required=False, min_value=1)
    operator_id = serializers.IntegerField(required=False, min_value=1)
    operator = serializers.CharField(required=False, allow_blank=False, max_length=150)
    module = serializers.CharField(required=False, allow_blank=False, max_length=50)
    action = serializers.CharField(required=False, allow_blank=False, max_length=80)
    result = serializers.ChoiceField(
        required=False,
        choices=OperationLog.RESULT_CHOICES,
    )
    keyword = serializers.CharField(required=False, allow_blank=False, max_length=100)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({"date_to": "结束日期不能早于开始日期"})
        return attrs
