"""Conservatively consolidate agentic findings before publishing a report."""

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

from .deduplication import finding_category
from .models import Finding, Severity


_SEVERITY = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
}
_REPOSITORY_EVIDENCE_TOOLS = {
    "read_file", "search_repository", "symbol", "git_context",
    "run_repository_checks", "test",
}
_EMPTY_OUTPUTS = {"", "[]", "{}", "null", "none"}


def _has_repository_evidence(finding: Finding) -> bool:
    """A changed line alone cannot establish a pre-existing caller contract."""
    for ref in finding.evidence_refs:
        if not isinstance(ref, dict):
            continue
        tool = str(ref.get("tool", ""))
        output = str(ref.get("output_preview", "")).strip().lower()
        if tool in _REPOSITORY_EVIDENCE_TOOLS and output not in _EMPTY_OUTPUTS:
            return True
    return False


def _identity(finding: Finding) -> Tuple[str, int, str, str]:
    rule_id = finding.rule_id.upper()
    if rule_id.startswith("CORR-EVAL-"):
        if rule_id.endswith("-RETURN"):
            return finding.path, finding.line, "correctness", "eval-return-contract"
        if rule_id.endswith("-EXC") and _has_repository_evidence(finding):
            return finding.path, finding.line, "correctness", "eval-exception-contract"
        return finding.path, finding.line, "correctness", "eval-compatibility"
    if rule_id.startswith(("SEC-", "CWE-")) or finding.source == "security":
        return finding.path, finding.line, "security", finding_category(finding)
    return finding.path, finding.line, "other", rule_id


def _quality(finding: Finding, identity: Tuple[str, int, str, str]) -> tuple:
    # The JSON input-format change follows directly from json.loads -> eval.
    # An unverified exception-contract claim is less direct evidence of impact.
    directness = int(
        identity[-1] == "eval-compatibility"
        and finding.rule_id.upper().endswith("-FORMAT")
    )
    detail = len(finding.explanation) + len(finding.fix) + len(finding.test)
    return directness, _SEVERITY[finding.severity], finding.confidence, detail


def consolidate_agentic_findings(
    findings: Iterable[Finding],
) -> Tuple[List[Finding], List[Dict[str, object]]]:
    """Keep independently supported defects and explain every suppressed item."""
    groups = defaultdict(list)
    suppressed: List[Dict[str, object]] = []
    for index, finding in enumerate(findings):
        rule_id = finding.rule_id.upper()
        reason = ""
        if rule_id == "CORR-EVAL-TESTS":
            reason = "test coverage belongs in test guidance, not a standalone defect"
        elif rule_id == "CORR-EVAL-RETURN" and not _has_repository_evidence(finding):
            reason = "return contract lacks repository evidence"
        if reason:
            suppressed.append({
                "index": index, "rule_id": finding.rule_id,
                "path": finding.path, "line": finding.line, "reason": reason,
            })
            continue
        groups[_identity(finding)].append((index, finding))

    kept = []
    for identity, candidates in groups.items():
        winner_index, winner = max(
            candidates, key=lambda item: _quality(item[1], identity),
        )
        kept.append(winner)
        for index, finding in candidates:
            if index != winner_index:
                suppressed.append({
                    "index": index, "rule_id": finding.rule_id,
                    "path": finding.path, "line": finding.line,
                    "reason": "same root cause as another published finding",
                    "kept_rule_id": winner.rule_id,
                })

    kept.sort(key=lambda item: (
        -_SEVERITY[item.severity], item.path, item.line, item.rule_id,
    ))
    suppressed.sort(key=lambda item: int(item["index"]))
    return kept, suppressed
