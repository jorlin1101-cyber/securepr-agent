import unittest

from securepr_agent.agentic_core import BoundedRole
from securepr_agent.runtime import ToolRegistry
from securepr_agent.telemetry import ExecutionLedger


class _MissingActionClient:
    def complete_json(self, _role, system, _user, _ledger, max_tokens=None):
        if 'top-level "action" key' not in system:
            raise AssertionError("role protocol was not included in the system prompt")
        return {"delegations": []}


class RoleProtocolTests(unittest.TestCase):
    def test_unambiguous_final_payload_without_action_is_normalized(self):
        role = BoundedRole("lead", "Delegate review work.", _MissingActionClient(), 1000, 10)
        result = role.run("{}", ToolRegistry(), ExecutionLedger("agentic"))
        self.assertEqual("final", result["action"])
