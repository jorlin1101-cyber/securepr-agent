import unittest

from securepr_agent.diff_parser import parse_unified_diff
from securepr_agent.models import Finding, Severity
from securepr_agent.reviewer import CompositeReviewer, LocalRuleReviewer
from securepr_agent.safety import SAFE_TEST_GUIDANCE, sanitize_guidance


class StaticReviewer:
    name = "static"

    def __init__(self, findings):
        self.findings = findings

    def review(self, diff, parsed):
        return list(self.findings)


class LocalReviewerTests(unittest.TestCase):
    def test_detects_security_findings_only_on_added_lines(self):
        diff = """--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
-eval(old_input)
+password = "super-secret"
+eval(user_input)
 safe = True
"""
        findings = LocalRuleReviewer().review(diff, parse_unified_diff(diff))
        self.assertEqual({"SEC-EVAL", "SEC-HARDCODED-SECRET"}, {item.rule_id for item in findings})
        self.assertTrue(all(item.line in {1, 2} for item in findings))

    def test_destructive_test_guidance_is_replaced(self):
        self.assertEqual(SAFE_TEST_GUIDANCE, sanitize_guidance('Run "rm -rf /" to verify the issue.'))
        self.assertEqual("Use a mocked input.", sanitize_guidance("Use a mocked input."))

    def test_semantic_duplicates_from_different_reviewers_are_merged(self):
        diff = """--- a/app.py
+++ b/app.py
@@ -0,0 +1 @@
+eval(user_input)
"""
        parsed = parse_unified_diff(diff)
        local = Finding(
            "SEC-EVAL", Severity.CRITICAL, "动态代码执行", "x" * 20,
            "app.py", 1, "eval(user_input)", "replace eval", "mock input", 0.9,
        )
        llm = Finding(
            "CWE-95", Severity.HIGH, "Arbitrary code execution via eval", "y" * 30,
            "app.py", 1, "eval(user_input)", "use a parser", "mock input", 0.95,
        )
        findings = CompositeReviewer([StaticReviewer([local]), StaticReviewer([llm])]).review(diff, parsed)
        self.assertEqual(1, len(findings))
        self.assertEqual("SEC-EVAL", findings[0].rule_id)

    def test_different_categories_on_the_same_line_are_preserved(self):
        diff = """--- a/app.py
+++ b/app.py
@@ -0,0 +1 @@
+dangerous_call(user_input)
"""
        parsed = parse_unified_diff(diff)
        eval_finding = Finding(
            "SEC-EVAL", Severity.CRITICAL, "Dynamic code execution", "x" * 20,
            "app.py", 1, "dangerous_call(user_input)", "use a parser", "mock input", 0.9,
        )
        secret_finding = Finding(
            "SEC-HARDCODED-SECRET", Severity.HIGH, "Hardcoded credential", "y" * 20,
            "app.py", 1, "dangerous_call(user_input)", "use a secret store", "mock input", 0.9,
        )
        findings = CompositeReviewer(
            [StaticReviewer([eval_finding]), StaticReviewer([secret_finding])]
        ).review(diff, parsed)
        self.assertEqual({"SEC-EVAL", "SEC-HARDCODED-SECRET"}, {item.rule_id for item in findings})


if __name__ == "__main__":
    unittest.main()

