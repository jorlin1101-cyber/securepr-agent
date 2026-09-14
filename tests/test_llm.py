import json
import unittest
from unittest.mock import patch

from securepr_agent.llm import JsonChatClient


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({
            "choices": [{"message": {"content": '{"action":"final"}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4},
        }).encode("utf-8")


class JsonChatClientTests(unittest.TestCase):
    def test_deepseek_json_call_disables_default_thinking(self):
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(json.loads(request.data))
            return _Response()

        client = JsonChatClient("https://api.deepseek.com", "test-key", "deepseek-flash", "deepseek")
        with patch("securepr_agent.llm.urllib.request.urlopen", side_effect=fake_urlopen):
            result = client.complete_json("lead", "Choose one action.", "Review this diff", max_tokens=400)

        self.assertEqual({"action": "final"}, result)
        self.assertEqual({"type": "disabled"}, requests[0]["thinking"])
        self.assertEqual({"type": "json_object"}, requests[0]["response_format"])
        self.assertIn("one complete JSON object", requests[0]["messages"][0]["content"])
        self.assertEqual(400, requests[0]["max_tokens"])
