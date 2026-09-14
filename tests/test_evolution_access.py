import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from securepr_agent.api import ApiHandler
from securepr_agent.config import Settings
from securepr_agent.service import ReviewService


class EvolutionAccessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        settings = Settings(
            host="127.0.0.1", port=0,
            db_path=os.path.join(self.directory.name, "test.db"),
            max_diff_bytes=10000, max_steps=8, timeout_seconds=10,
            llm_base_url="", llm_api_key="", llm_model="",
            github_webhook_secret="", github_token="", auto_post_review=False,
            auth_required=True, auth_secret="test-session-secret-at-least-32-bytes",
            guest_access_enabled=True,
            bootstrap_admin_username="demo-admin",
            bootstrap_admin_password="test-password-123",
        )
        self.service = ReviewService(settings)
        handler = type("QuietApiHandler", (ApiHandler,), {
            "service": self.service,
            "settings": settings,
            "log_message": lambda *_args: None,
        })
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.service.queue.close()
        self.directory.cleanup()

    def request(self, path, token="", payload=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_guest_can_read_status_but_only_admin_can_run_replay(self):
        _, guest = self.request("/v1/auth/guest", payload={})
        guest_token = guest["access_token"]
        code, status = self.request("/v1/evolution/status", guest_token)
        self.assertEqual(200, code)
        self.assertEqual("guest", status["access"]["role"])
        self.assertFalse(status["access"]["can_run_replay"])
        self.assertFalse(status["access"]["can_view_failures"])
        self.assertEqual(403, self.request("/api/failures", guest_token)[0])
        self.assertEqual(403, self.request(
            "/v1/evolution/propose", guest_token,
            {"skill_name": "llm-review", "prompt": "sample"},
        )[0])

        _, admin = self.request("/v1/auth/login", payload={
            "username": "demo-admin", "password": "test-password-123",
        })
        code, status = self.request("/v1/evolution/status", admin["access_token"])
        self.assertEqual(200, code)
        self.assertTrue(status["access"]["can_run_replay"])
        self.assertTrue(status["access"]["can_view_failures"])
        self.assertEqual(200, self.request("/api/failures", admin["access_token"])[0])
