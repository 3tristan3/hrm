import json

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Application,
    ApplicationAttachment,
    InterviewCandidate,
    Job,
    Region,
    RegionField,
)
from .serializers import (
    ApplicationAdminListSerializer,
    ApplicationAdminSerializer,
    ApplicationAttachmentSerializer,
    ApplicationAttachmentUploadSerializer,
    ApplicationCreateSerializer,
    AdminPasswordResetSerializer,
    AdminUserSerializer,
    ChangePasswordSerializer,
    InterviewCandidateBatchAddSerializer,
    InterviewCandidateBatchRemoveSerializer,
    InterviewCandidateListSerializer,
    JobAdminSerializer,
    JobBatchStatusSerializer,
    JobSerializer,
    LoginSerializer,
    MeSerializer,
    RegisterSerializer,
    RegionAdminSerializer,
    RegionFieldAdminSerializer,
    RegionSerializer,
)


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request):
        return Response({"status": "ok"})


class AdminScopedMixin:
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _user_region_scope(self):
        user = self.request.user
        profile = getattr(user, "profile", None)
        if user.is_superuser:
            return None
        if profile and profile.can_view_all:
            return None
        return profile.region_id if profile else -1

    def _scope_queryset(self, queryset):
        region_id = self._user_region_scope()
        if region_id:
            return queryset.filter(region_id=region_id)
        return queryset

    def _check_region_payload(self, request):
        """校验非全局账号只能操作所属地区的数据，返回 Response 或 None。"""
        region_id = self._user_region_scope()
        if region_id is None:
            return None
        payload_region = request.data.get("region")
        try:
            payload_region = int(payload_region)
        except (TypeError, ValueError):
            payload_region = None
        if payload_region != region_id:
            return Response(
                {"error": "只能维护所属地区的岗位"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


class RegionListView(APIView):
    def get(self, request: Request):
        queryset = Region.objects.filter(is_active=True).prefetch_related("fields")
        serializer = RegionSerializer(queryset, many=True)
        return Response(serializer.data)


class JobListView(APIView):
    def get(self, request: Request):
        queryset = Job.objects.filter(is_active=True)
        region_id = request.query_params.get("region_id")
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        serializer = JobSerializer(queryset, many=True)
        return Response(serializer.data)


class JobDetailView(APIView):
    def get(self, request: Request, pk: int):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        serializer = JobSerializer(job)
        return Response(serializer.data)


class ApplicationCreateView(APIView):
    def _coerce_payload(self, data):
        payload = data.copy() if hasattr(data, "copy") else dict(data)
        for key in ("education_history", "work_history", "family_members", "extra_fields"):
            value = payload.get(key)
            if isinstance(value, str):
                try:
                    payload[key] = json.loads(value)
                except json.JSONDecodeError:
                    pass
        for key in ("available_date", "birth_month", "graduation_date"):
            if payload.get(key) == "":
                payload[key] = None
        return payload

    def post(self, request: Request):
        payload = self._coerce_payload(request.data)
        serializer = ApplicationCreateSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        # region / job 由 validate() 写入，region_id / job_id 是序列化器字段不需要
        create_kwargs = {k: v for k, v in data.items() if k not in ("region_id", "job_id")}
        application = Application.objects.create(**create_kwargs)

        return Response(
            {"message": "提交成功", "applicationId": application.pk},
            status=status.HTTP_201_CREATED,
        )


class ApplicationSubmitView(ApplicationCreateView):
    pass


class MockOAView(APIView):
    def post(self, request: Request):
        payload = request.data
        return Response(
            {
                "requestId": "MOCK-REQUEST-001",
                "received": payload,
            },
            status=status.HTTP_201_CREATED,
        )


class ApplicationAttachmentListCreateView(APIView):
    def get(self, request: Request, pk: int):
        application = get_object_or_404(Application, pk=pk)
        serializer = ApplicationAttachmentSerializer(
            application.attachments.all(), many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request: Request, pk: int):
        application = get_object_or_404(Application, pk=pk)
        serializer = ApplicationAttachmentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        category = serializer.validated_data["category"]
        files = request.FILES.getlist("file")
        if not files:
            return Response(
                {"error": "未上传文件"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if category != "other" and len(files) > 1:
            return Response(
                {"error": "该附件类型仅支持上传单个文件"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if category != "other":
            ApplicationAttachment.objects.filter(
                application=application, category=category
            ).delete()
        attachments = [
            ApplicationAttachment.objects.create(
                application=application, category=category, file=upload
            )
            for upload in files
        ]
        output = ApplicationAttachmentSerializer(
            attachments, many=True, context={"request": request}
        )
        return Response(output.data, status=status.HTTP_201_CREATED)


class RegisterView(APIView):
    def post(self, request: Request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = serializer.save()
        return Response(
            {
                "token": result["token"],
                "username": result["user"].username,
                "region": result["region"].id,
                "can_view_all": result["can_view_all"],
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    def post(self, request: Request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "登录失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        profile = getattr(user, "profile", None)
        return Response(
            {
                "token": token.key,
                "username": user.username,
                "region": profile.region_id if profile else None,
                "can_view_all": profile.can_view_all if profile else False,
            }
        )


class MeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        profile = getattr(request.user, "profile", None)
        serializer = MeSerializer(
            {
                "username": request.user.username,
                "is_superuser": request.user.is_superuser,
                "profile": profile,
            }
        )
        return Response(serializer.data)


User = get_user_model()


class AdminUserListView(AdminScopedMixin, APIView):
    def get(self, request: Request):
        if not request.user.is_superuser:
            return Response({"error": "无权限访问"}, status=status.HTTP_403_FORBIDDEN)
        queryset = User.objects.select_related("profile__region").order_by("username")
        serializer = AdminUserSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminUserPasswordView(AdminScopedMixin, APIView):
    def post(self, request: Request, pk: int):
        if not request.user.is_superuser:
            return Response({"error": "无权限操作"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=pk)
        serializer = AdminPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        return Response({"message": "密码已更新"})


class AdminUserDetailView(AdminScopedMixin, APIView):
    def delete(self, request: Request, pk: int):
        if not request.user.is_superuser:
            return Response({"error": "无权限操作"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            return Response({"error": "不能删除系统管理员账号"}, status=status.HTTP_400_BAD_REQUEST)
        if user.pk == request.user.pk:
            return Response({"error": "不能删除当前登录账号"}, status=status.HTTP_400_BAD_REQUEST)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"error": "原密码不正确"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"message": "密码已更新"})


class _RegionAdminQuerysetMixin(AdminScopedMixin):
    """共享 Region 查询集逻辑。"""
    serializer_class = RegionAdminSerializer

    def get_queryset(self):
        region_id = self._user_region_scope()
        if region_id:
            return Region.objects.filter(id=region_id)
        return Region.objects.all()


class AdminRegionListView(_RegionAdminQuerysetMixin, generics.ListCreateAPIView):

    def create(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区为系统固定配置，无法新增"},
            status=status.HTTP_403_FORBIDDEN,
        )


class AdminRegionDetailView(_RegionAdminQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):

    def update(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区为系统固定配置，无法修改"},
            status=status.HTTP_403_FORBIDDEN,
        )

    def destroy(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区为系统固定配置，无法删除"},
            status=status.HTTP_403_FORBIDDEN,
        )


class AdminRegionFieldListView(AdminScopedMixin, generics.ListCreateAPIView):
    queryset = RegionField.objects.all()
    serializer_class = RegionFieldAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(RegionField.objects.all())

    def create(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区字段为系统固定配置，无法新增"},
            status=status.HTTP_403_FORBIDDEN,
        )


class AdminRegionFieldDetailView(AdminScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = RegionField.objects.all()
    serializer_class = RegionFieldAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(RegionField.objects.all())

    def update(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区字段为系统固定配置，无法修改"},
            status=status.HTTP_403_FORBIDDEN,
        )

    def destroy(self, request: Request, *args, **kwargs):
        return Response(
            {"error": "地区字段为系统固定配置，无法删除"},
            status=status.HTTP_403_FORBIDDEN,
        )


class AdminJobListView(AdminScopedMixin, generics.ListCreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(Job.objects.all())

    def create(self, request: Request, *args, **kwargs):
        err = self._check_region_payload(request)
        if err:
            return err
        return super().create(request, *args, **kwargs)


class AdminJobDetailView(AdminScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobAdminSerializer

    def get_queryset(self):
        return self._scope_queryset(Job.objects.all())

    def update(self, request: Request, *args, **kwargs):
        err = self._check_region_payload(request)
        if err:
            return err
        return super().update(request, *args, **kwargs)

    def destroy(self, request: Request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "该岗位已有应聘记录，无法删除"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AdminJobBatchStatusView(AdminScopedMixin, APIView):
    def post(self, request: Request):
        serializer = JobBatchStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job_ids = serializer.validated_data["job_ids"]
        is_active = serializer.validated_data["is_active"]

        queryset = self._scope_queryset(Job.objects.filter(id__in=job_ids))
        allowed_ids = set(queryset.values_list("id", flat=True))
        missing_ids = sorted(set(job_ids) - allowed_ids)
        if missing_ids:
            return Response(
                {
                    "error": "包含无权限或不存在的岗位",
                    "details": {"job_ids": missing_ids},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = queryset.update(is_active=is_active)
        return Response(
            {
                "updated": updated,
                "total": len(job_ids),
                "is_active": is_active,
            }
        )


class _ApplicationAdminQuerysetMixin(AdminScopedMixin):
    """共享 Application 查询集逻辑。"""

    def get_queryset(self):
        queryset = Application.objects.select_related("region", "job").prefetch_related(
            Prefetch(
                "attachments",
                queryset=ApplicationAttachment.objects.filter(category="photo").order_by("-created_at"),
                to_attr="photo_attachments",
            )
        )
        return self._scope_queryset(queryset)


class AdminApplicationListView(_ApplicationAdminQuerysetMixin, generics.ListAPIView):
    serializer_class = ApplicationAdminListSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(job__is_active=True)
        job_id = self.request.query_params.get("job_id")
        region_id = self.request.query_params.get("region_id")
        job = self.request.query_params.get("job")
        region = self.request.query_params.get("region")
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if job:
            queryset = queryset.filter(job__title__icontains=job)
        if region:
            queryset = queryset.filter(region__name__icontains=region)
        return queryset


class AdminApplicationDetailView(_ApplicationAdminQuerysetMixin, generics.RetrieveAPIView):
    serializer_class = ApplicationAdminSerializer


class _InterviewCandidateAdminQuerysetMixin(AdminScopedMixin):
    def get_queryset(self):
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


class AdminInterviewCandidateListView(_InterviewCandidateAdminQuerysetMixin, generics.ListAPIView):
    serializer_class = InterviewCandidateListSerializer


class AdminInterviewCandidateDetailView(
    _InterviewCandidateAdminQuerysetMixin, generics.DestroyAPIView
):
    serializer_class = InterviewCandidateListSerializer


class AdminInterviewCandidateBatchAddView(AdminScopedMixin, APIView):
    def post(self, request: Request):
        serializer = InterviewCandidateBatchAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application_ids = serializer.validated_data["application_ids"]
        region_id = self._user_region_scope()
        app_queryset = Application.objects.filter(id__in=application_ids)
        if region_id:
            app_queryset = app_queryset.filter(region_id=region_id)

        allowed_ids = set(app_queryset.values_list("id", flat=True))
        missing_ids = sorted(set(application_ids) - allowed_ids)
        if missing_ids:
            return Response(
                {
                    "error": "包含无权限或不存在的应聘记录",
                    "details": {"application_ids": missing_ids},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_before = set(
            InterviewCandidate.objects.filter(application_id__in=application_ids).values_list(
                "application_id", flat=True
            )
        )

        to_create = [
            InterviewCandidate(application_id=application_id)
            for application_id in application_ids
            if application_id not in existing_before
        ]
        if to_create:
            InterviewCandidate.objects.bulk_create(to_create, ignore_conflicts=True)

        existing_after = set(
            InterviewCandidate.objects.filter(application_id__in=application_ids).values_list(
                "application_id", flat=True
            )
        )
        added_count = len(existing_after - existing_before)

        return Response(
            {
                "added": added_count,
                "existing": len(existing_before),
                "total": len(application_ids),
            }
        )


class AdminInterviewCandidateBatchRemoveView(AdminScopedMixin, APIView):
    def post(self, request: Request):
        serializer = InterviewCandidateBatchRemoveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        interview_candidate_ids = serializer.validated_data["interview_candidate_ids"]
        queryset = InterviewCandidate.objects.filter(id__in=interview_candidate_ids)
        region_id = self._user_region_scope()
        if region_id:
            queryset = queryset.filter(application__region_id=region_id)

        allowed_ids = set(queryset.values_list("id", flat=True))
        missing_ids = sorted(set(interview_candidate_ids) - allowed_ids)
        if missing_ids:
            return Response(
                {
                    "error": "包含无权限或不存在的拟面试人员记录",
                    "details": {"interview_candidate_ids": missing_ids},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        removed_count = queryset.count()
        queryset.delete()
        return Response(
            {
                "removed": removed_count,
                "total": len(interview_candidate_ids),
            }
        )
