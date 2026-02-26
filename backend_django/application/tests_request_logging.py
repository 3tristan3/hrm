"""请求日志中间件测试：验证 request_id 透传与状态日志落盘。"""

from django.test import TestCase
from rest_framework.test import APIClient


class RequestLoggingMiddlewareTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_response_contains_generated_request_id(self):
        with self.assertLogs("application.request", level="INFO") as logs:
            response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("X-Request-ID"))
        self.assertTrue(
            any("backend_request_complete" in entry and "status=200" in entry for entry in logs.output)
        )

    def test_health_response_preserves_incoming_request_id(self):
        incoming_request_id = "mobile-scan-req-001"
        response = self.client.get("/api/health/", HTTP_X_REQUEST_ID=incoming_request_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Request-ID"), incoming_request_id)

    def test_not_found_request_logs_warning(self):
        with self.assertLogs("application.request", level="WARNING") as logs:
            response = self.client.get("/api/not-exists/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(any("status=404" in entry for entry in logs.output))
