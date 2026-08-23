import os
import tempfile
import unittest
from unittest.mock import patch

from securepr_agent.config import load_dotenv


class DotenvTests(unittest.TestCase):
    def test_loads_valid_assignments_and_quoted_values(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write("# comment\n")
            handle.write("export SECUREPR_LLM_PROVIDER=deepseek\n")
            handle.write('SECUREPR_DEEPSEEK_API_KEY="test-key"\n')
            handle.write("invalid line\n")
            path = handle.name
        try:
            with patch.dict(os.environ, {}, clear=True):
                load_dotenv([path])
                self.assertEqual("deepseek", os.environ["SECUREPR_LLM_PROVIDER"])
                self.assertEqual("test-key", os.environ["SECUREPR_DEEPSEEK_API_KEY"])
        finally:
            os.unlink(path)

    def test_process_environment_has_priority(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write("SECUREPR_LLM_PROVIDER=deepseek\n")
            path = handle.name
        try:
            with patch.dict(os.environ, {"SECUREPR_LLM_PROVIDER": "custom"}, clear=True):
                load_dotenv([path])
                self.assertEqual("custom", os.environ["SECUREPR_LLM_PROVIDER"])
        finally:
            os.unlink(path)
