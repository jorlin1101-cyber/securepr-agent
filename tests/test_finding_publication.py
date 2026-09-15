import unittest

from securepr_agent.finding_publication import consolidate_agentic_findings
from securepr_agent.models import Finding, Severity


def finding(rule_id, severity=Severity.HIGH, confidence=0.9, refs=None):
    return Finding(
        rule_id=rule_id, severity=severity, title=rule_id,
        explanation="Review the changed parser behavior.",
        path="app/parser.py", line=4, evidence="return eval(raw)",
        fix="Restore json.loads(raw).", test="Test JSON inputs.",
        confidence=confidence, evidence_refs=refs or [],
        call_chain=[{"path": "app/parser.py", "line": 4, "symbol": "parse_user_input"}],
        source="correctness-reliability",
    )


class FindingPublicationTests(unittest.TestCase):
    def test_eval_example_publishes_two_independent_issues(self):
        candidates = [
            finding("SEC-EVAL", Severity.CRITICAL, 0.95),
            finding("CORR-EVAL-EXC", confidence=0.99),
            finding("CORR-EVAL-FORMAT", confidence=0.70),
            finding("CORR-EVAL-RETURN", confidence=0.99),
            finding("CORR-EVAL-TESTS", Severity.MEDIUM, 0.99),
        ]

        published, suppressed = consolidate_agentic_findings(candidates)

        self.assertEqual(
            ["SEC-EVAL", "CORR-EVAL-FORMAT"],
            [item.rule_id for item in published],
        )
        compatibility = published[1]
        self.assertEqual(Severity.HIGH, compatibility.severity)
        self.assertNotIn("security", compatibility.explanation.lower())
        self.assertNotIn("arbitrary", compatibility.explanation.lower())
        self.assertIn("true, false and null", compatibility.explanation)
        self.assertEqual(
            {"CORR-EVAL-EXC", "CORR-EVAL-RETURN", "CORR-EVAL-TESTS"},
            {item["rule_id"] for item in suppressed},
        )
        self.assertEqual(
            "CORR-EVAL-FORMAT",
            next(
                item for item in suppressed if item["rule_id"] == "CORR-EVAL-EXC"
            )["kept_rule_id"],
        )

    def test_distinct_security_categories_on_same_eval_line_survive(self):
        published, suppressed = consolidate_agentic_findings([
            finding("SEC-EVAL", Severity.CRITICAL),
            finding("CWE-95", Severity.HIGH),
            finding("SEC-HARDCODED-SECRET", Severity.HIGH),
            finding("CORR-EVAL-FORMAT"),
        ])

        self.assertEqual(
            {"SEC-EVAL", "SEC-HARDCODED-SECRET", "CORR-EVAL-FORMAT"},
            {item.rule_id for item in published},
        )
        self.assertEqual(["CWE-95"], [item["rule_id"] for item in suppressed])

    def test_repository_supported_contracts_are_not_discarded(self):
        exception_ref = [{
            "tool": "read_file", "evidence_id": "read_file:caller",
            "output_preview": "except json.JSONDecodeError: return None",
        }]
        return_ref = [{
            "tool": "read_file", "evidence_id": "read_file:signature",
            "output_preview": "def parse_user_input(raw: str) -> dict:",
        }]
        published, suppressed = consolidate_agentic_findings([
            finding("CORR-EVAL-FORMAT"),
            finding("CORR-EVAL-EXC", refs=exception_ref),
            finding("CORR-EVAL-RETURN", refs=return_ref),
            finding("CORR-EVAL-TESTS", refs=return_ref),
        ])

        self.assertEqual(
            {"CORR-EVAL-FORMAT", "CORR-EVAL-EXC", "CORR-EVAL-RETURN"},
            {item.rule_id for item in published},
        )
        self.assertEqual(["CORR-EVAL-TESTS"], [item["rule_id"] for item in suppressed])

    def test_empty_repository_search_is_not_contract_evidence(self):
        empty_search = [{
            "tool": "search_repository", "evidence_id": "search_repository:empty",
            "output_preview": "[]",
        }]
        published, suppressed = consolidate_agentic_findings([
            finding("CORR-EVAL-RETURN", refs=empty_search),
        ])
        self.assertEqual([], published)
        self.assertEqual("return contract lacks repository evidence", suppressed[0]["reason"])

    def test_single_eval_contract_is_published_as_compatibility_only(self):
        contract = finding("CORR-EVAL-CONTRACT", Severity.CRITICAL)
        contract.explanation = "Compatibility, return semantics, and arbitrary code execution."

        published, suppressed = consolidate_agentic_findings([contract])

        self.assertEqual([], suppressed)
        self.assertEqual("CORR-EVAL-FORMAT", published[0].rule_id)
        self.assertEqual(Severity.HIGH, published[0].severity)
        self.assertNotIn("code execution", published[0].explanation.lower())


if __name__ == "__main__":
    unittest.main()
