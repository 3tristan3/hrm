"""OA 对接客户端：封装流程发起请求、鉴权参数与错误处理。"""
import requests
from django.conf import settings


class OAConfigError(Exception):
    pass


class OARequestError(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


def build_main_data(data):
    main_data = []
    for api_field, oa_field in settings.OA_FIELD_MAPPING.items():
        if api_field in data:
            main_data.append(
                {
                    "fieldName": oa_field,
                    "fieldValue": data[api_field],
                }
            )
    return main_data


def extract_request_id(payload):
    if isinstance(payload, dict):
        for key in ("requestId", "requestid", "requestID"):
            if key in payload:
                return str(payload[key])
        for nested_key in ("data", "result"):
            if nested_key in payload:
                request_id = extract_request_id(payload[nested_key])
                if request_id:
                    return request_id
    return None


class OAClient:
    def __init__(self):
        if not settings.OA_API_URL:
            raise OAConfigError("OA_API_URL 未配置")
        if not settings.OA_WORKFLOW_ID:
            raise OAConfigError("OA_WORKFLOW_ID 未配置")
        if not settings.OA_CREATOR_ID:
            raise OAConfigError("OA_CREATOR_ID 未配置")

        self.api_url = settings.OA_API_URL
        self.workflow_id = settings.OA_WORKFLOW_ID
        self.creator_id = settings.OA_CREATOR_ID
        self.timeout = settings.OA_REQUEST_TIMEOUT

    def create_workflow(self, data):
        request_name = settings.OA_REQUEST_NAME_TEMPLATE.format(
            name=data.get("name", "")
        )
        payload = {
            "workflowId": self.workflow_id,
            "creatorId": self.creator_id,
            "requestName": request_name,
            "mainData": build_main_data(data),
        }

        try:
            response = requests.post(
                self.api_url, json=payload, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise OARequestError("调用OA接口失败", response=str(exc)) from exc

        if not response.ok:
            raise OARequestError(
                f"OA接口返回失败: {response.status_code}",
                response=response.text,
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise OARequestError("OA接口返回非JSON", response=response.text) from exc

        request_id = extract_request_id(body)
        if not request_id:
            raise OARequestError("OA接口未返回流程ID", response=body)
        return request_id
