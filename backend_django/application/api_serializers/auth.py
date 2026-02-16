"""按职责拆分的序列化器模块。"""
from .shared import *

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    region_id = serializers.IntegerField()

    def validate_username(self, value):
        normalized = (value or "").strip()
        if not normalized:
            raise serializers.ValidationError("账号不能为空")
        if User.objects.filter(username__iexact=normalized).exists():
            raise serializers.ValidationError("账号已存在")
        return normalized

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate_region_id(self, value):
        if not Region.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("地区不存在")
        return value

    def create(self, validated_data):
        username = validated_data["username"]
        password = validated_data["password"]
        region = Region.objects.get(id=validated_data["region_id"])

        user = User.objects.create_user(username=username, password=password)
        can_view_all = False
        UserProfile.objects.create(user=user, region=region, can_view_all=can_view_all)
        token, _ = Token.objects.get_or_create(user=user)
        return {"token": token.key, "user": user, "region": region, "can_view_all": can_view_all}

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = (attrs.get("username") or "").strip()
        password = attrs.get("password") or ""
        if not username or not password:
            raise serializers.ValidationError("账号或密码错误")
        matched_user = User.objects.filter(username__iexact=username).first()
        auth_username = matched_user.username if matched_user else username
        user = authenticate(username=auth_username, password=password)
        if not user:
            raise serializers.ValidationError("账号或密码错误")
        if not user.is_active:
            raise serializers.ValidationError("账号已禁用")
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
    password = serializers.CharField(min_length=8, max_length=128)

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8, max_length=128)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
