"""按职责拆分的视图模块。"""
import logging

from . import shared as shared_views
from .shared import *

logger = logging.getLogger(__name__)

class RegionListView(APIView):
    def get(self, request: Request):
        queryset = Region.objects.filter(is_active=True).prefetch_related("fields")
        serializer = RegionSerializer(queryset, many=True)
        return Response(serializer.data)

class JobListView(APIView):
    def get(self, request: Request):
        queryset = Job.objects.filter(is_active=True, is_deleted=False)
        region_id = request.query_params.get("region_id")
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        serializer = JobSerializer(queryset, many=True)
        return Response(serializer.data)

class JobDetailView(APIView):
    def get(self, request: Request, pk: int):
        job = get_object_or_404(Job, pk=pk, is_active=True, is_deleted=False)
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
            {
                "message": "提交成功",
                "applicationId": application.pk,
                "attachmentToken": application.attachment_token,
            },
            status=status.HTTP_201_CREATED,
        )

class ApplicationSubmitView(ApplicationCreateView):
    pass

class ApplicationTokenAccessMixin:
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [AllowAny]

    @staticmethod
    def _not_found_response():
        return Response({"error": "记录不存在"}, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def _is_admin_request(request: Request) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)

    @staticmethod
    def _extract_token(request: Request):
        header_value = (request.headers.get(ATTACHMENT_TOKEN_HEADER) or "").strip()
        if header_value:
            return header_value
        query_value = (request.query_params.get("token") or "").strip()
        if query_value:
            return query_value
        data_value = (request.data.get("attachment_token") or "").strip() if hasattr(request, "data") else ""
        return data_value

    def _has_valid_token(self, request: Request, application: Application) -> bool:
        token = self._extract_token(request)
        if not token:
            return False
        return constant_time_compare(str(application.attachment_token), token)

    def _resolve_accessible_application(self, request: Request, pk: int):
        application = get_object_or_404(Application, pk=pk)
        if self._is_admin_request(request) or self._has_valid_token(request, application):
            return application
        return None

class ApplicationAttachmentListCreateView(ApplicationTokenAccessMixin, APIView):
    @staticmethod
    def _request_meta(request: Request):
        forwarded_for = str(request.META.get("HTTP_X_FORWARDED_FOR", "") or "").strip()
        remote_addr = forwarded_for.split(",")[0].strip() if forwarded_for else str(
            request.META.get("REMOTE_ADDR", "") or ""
        ).strip()
        return {
            "request_id": request_id_from_request(request),
            "remote_addr": remote_addr,
            "user_agent": str(request.META.get("HTTP_USER_AGENT", "") or "")[:180],
        }

    def _log_upload_failure(
        self,
        request: Request,
        *,
        application_id: int | None,
        category: str,
        reason: str,
        status_code: int,
        details=None,
    ):
        meta = self._request_meta(request)
        logger.warning(
            "application_attachment_upload_failed reason=%s status=%s app_id=%s category=%s request_id=%s ip=%s details=%r",
            reason,
            status_code,
            application_id,
            category,
            meta["request_id"],
            meta["remote_addr"],
            details,
        )

    def get(self, request: Request, pk: int):
        application = self._resolve_accessible_application(request, pk)
        if not application:
            return self._not_found_response()
        serializer = ApplicationAttachmentSerializer(
            application.attachments.all(), many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request: Request, pk: int):
        application = self._resolve_accessible_application(request, pk)
        if not application:
            self._log_upload_failure(
                request,
                application_id=pk,
                category=str(request.data.get("category") or ""),
                reason="application_not_found_or_token_invalid",
                status_code=status.HTTP_404_NOT_FOUND,
            )
            return self._not_found_response()
        serializer = ApplicationAttachmentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            self._log_upload_failure(
                request,
                application_id=application.pk,
                category=str(request.data.get("category") or ""),
                reason="invalid_payload",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )
            return Response(
                {"error": "参数校验失败", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        category = serializer.validated_data["category"]
        files = request.FILES.getlist("file")
        if not files:
            self._log_upload_failure(
                request,
                application_id=application.pk,
                category=category,
                reason="missing_files",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(
                {"error": "未上传文件"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if category != "other" and len(files) > 1:
            self._log_upload_failure(
                request,
                application_id=application.pk,
                category=category,
                reason="too_many_files_for_single_category",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"file_count": len(files)},
            )
            return Response(
                {"error": "该附件类型仅支持上传单个文件"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_file_mb, max_total_mb, max_file_bytes, max_total_bytes = shared_views._resolve_attachment_limits()
        oversized_files = [upload.name for upload in files if shared_views._safe_file_size(upload) > max_file_bytes]
        if oversized_files:
            self._log_upload_failure(
                request,
                application_id=application.pk,
                category=category,
                reason="single_file_size_exceeded",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={
                    "max_file_mb": max_file_mb,
                    "oversized_files": oversized_files,
                },
            )
            return Response(
                {
                    "error": f"单个文件不能超过{max_file_mb}MB",
                    "details": {"file": [f"超出大小限制: {name}" for name in oversized_files]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        incoming_total_bytes = sum(shared_views._safe_file_size(upload) for upload in files)
        existing_attachments = list(application.attachments.all())
        existing_total_bytes = sum(shared_views._safe_file_size(item.file) for item in existing_attachments)
        replaced_bytes = 0
        if category != "other":
            replaced_bytes = sum(
                shared_views._safe_file_size(item.file)
                for item in existing_attachments
                if item.category == category
            )
        projected_total_bytes = max(existing_total_bytes - replaced_bytes, 0) + incoming_total_bytes
        if projected_total_bytes > max_total_bytes:
            self._log_upload_failure(
                request,
                application_id=application.pk,
                category=category,
                reason="total_attachment_size_exceeded",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={
                    "max_total_mb": max_total_mb,
                    "existing_total_bytes": existing_total_bytes,
                    "incoming_total_bytes": incoming_total_bytes,
                    "projected_total_bytes": projected_total_bytes,
                },
            )
            return Response(
                {"error": f"附件总大小不能超过{max_total_mb}MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
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
        except Exception:
            meta = self._request_meta(request)
            logger.exception(
                "application_attachment_upload_exception app_id=%s category=%s request_id=%s ip=%s",
                application.pk,
                category,
                meta["request_id"],
                meta["remote_addr"],
            )
            return Response(
                {"error": "附件上传失败，请稍后重试"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        output = ApplicationAttachmentSerializer(
            attachments, many=True, context={"request": request}
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

class ApplicationDiscardView(ApplicationTokenAccessMixin, APIView):
    def post(self, request: Request, pk: int):
        application = self._resolve_accessible_application(request, pk)
        if not application:
            return self._not_found_response()
        if hasattr(application, "interview_candidate"):
            return Response(
                {"error": "记录已进入面试流程，无法撤销"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            for item in application.attachments.all():
                try:
                    item.file.delete(save=False)
                except Exception:
                    pass
            application.delete()
        return Response({"message": "草稿已撤销"})
