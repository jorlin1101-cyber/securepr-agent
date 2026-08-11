import re
from typing import Pattern, Tuple


SAFE_TEST_GUIDANCE = (
    "请在隔离的测试环境中使用无副作用的模拟输入验证该风险；"
    "不要执行删除文件、清空数据或系统级命令。"
)


_DESTRUCTIVE_PATTERNS: Tuple[Pattern[str], ...] = (
    re.compile(r"\brm\s+-(?:[a-z]*r[a-z]*f|[a-z]*f[a-z]*r)[a-z]*\s+", re.IGNORECASE),
    re.compile(r"\bremove-item\b[^\n]{0,200}\b-(?:recurse|r)\b", re.IGNORECASE),
    re.compile(r"\b(?:del|rmdir)\s+/[sq]\b", re.IGNORECASE),
    re.compile(r"\bformat\s+[a-z]:", re.IGNORECASE),
    re.compile(r"\bmkfs(?:\.[a-z0-9]+)?\b", re.IGNORECASE),
    re.compile(r"\bdd\s+[^\n]{0,200}\bof=/dev/", re.IGNORECASE),
    re.compile(r"\b(?:drop\s+database|truncate\s+table)\b", re.IGNORECASE),
    re.compile(r"\b(?:shutdown|reboot|poweroff)\b", re.IGNORECASE),
)


def contains_destructive_command(value: object) -> bool:
    text = str(value or "")
    return any(pattern.search(text) for pattern in _DESTRUCTIVE_PATTERNS)


def sanitize_guidance(value: object, limit: int = 2000) -> str:
    text = str(value or "")[:limit]
    if contains_destructive_command(text):
        return SAFE_TEST_GUIDANCE
    return text
