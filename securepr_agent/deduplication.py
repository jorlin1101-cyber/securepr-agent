import re
from typing import Dict, Iterable, List, Tuple

from .models import Finding, Severity


_CATEGORY_PATTERNS = (
    ("dynamic-code-execution", re.compile(r"(?:sec-eval|cwe-95|\beval\b|\bexec\b|dynamic code|动态代码)", re.IGNORECASE)),
    ("command-injection", re.compile(r"(?:sec-subprocess-shell|cwe-78|command injection|shell\s*=\s*true|命令注入)", re.IGNORECASE)),
    ("hardcoded-secret", re.compile(r"(?:sec-hardcoded-secret|cwe-798|hardcoded|credential|password|secret|硬编码|凭据)", re.IGNORECASE)),
    ("sql-injection", re.compile(r"(?:sec-sql-concat|cwe-89|sql injection|sql 注入)", re.IGNORECASE)),
    ("unsafe-deserialization", re.compile(r"(?:sec-pickle-deserialize|cwe-502|pickle|deserial|反序列化)", re.IGNORECASE)),
    ("broad-exception", re.compile(r"(?:rel-empty-except|broad exception|异常捕获)", re.IGNORECASE)),
    ("debug-output", re.compile(r"(?:rel-debug-print|debug output|console\.log|调试输出)", re.IGNORECASE)),
)

_SEVERITY_SCORE = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
}


def finding_category(finding: Finding) -> str:
    searchable = " ".join((
        finding.rule_id,
        finding.title,
        finding.explanation,
        finding.evidence,
    ))
    for category, pattern in _CATEGORY_PATTERNS:
        if pattern.search(searchable):
            return category
    fallback = re.sub(r"[^a-z0-9]+", "-", finding.rule_id.lower()).strip("-")
    return fallback or "uncategorized"


def finding_identity(finding: Finding) -> Tuple[str, int, str]:
    return finding.path, finding.line, finding_category(finding)


def _quality(finding: Finding) -> Tuple[int, float, int]:
    detail_length = len(finding.explanation) + len(finding.fix) + len(finding.test)
    return _SEVERITY_SCORE[finding.severity], finding.confidence, detail_length


def deduplicate_findings(findings: Iterable[Finding]) -> List[Finding]:
    merged: Dict[Tuple[str, int, str], Finding] = {}
    for finding in findings:
        identity = finding_identity(finding)
        current = merged.get(identity)
        if current is None or _quality(finding) > _quality(current):
            merged[identity] = finding
    return list(merged.values())
