"""Conservative, offline audit for generic public-release risks."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_SIZE = 2_000_000
IGNORED_PARTS = {".git", ".pytest_cache", "__pycache__", ".venv", "build", "dist"}
BLOCKED_SUFFIXES = {
    ".pdf",
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".parquet",
    ".arrow",
    ".feather",
    ".npy",
    ".npz",
    ".pt",
    ".pth",
    ".safetensors",
    ".bin",
    ".gguf",
    ".onnx",
    ".pkl",
    ".pickle",
    ".joblib",
    ".docx",
    ".xlsx",
    ".xls",
    ".pptx",
}

SECRET_PATTERNS = [
    (re.compile(r"(?i)\b(?:sk|rk)-[A-Za-z0-9]{16,}\b"), "secret-like token"),
    (re.compile(r"(?i)\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{20,}\b"), "GitHub token"),
    (re.compile(r"(?i)\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "GitHub token"),
    (re.compile(r"(?i)\bxox[baprs]-[A-Za-z0-9-]{16,}\b"), "Slack token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "cloud access key"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b"), "Bearer token"),
    (
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
            r"\s*[:=]\s*['\"][^'\"]{12,}['\"]"
        ),
        "credential assignment",
    ),
]

_HOME_PREFIX = "/" + "home/"
_USERS_PREFIX = "/" + "Users/"

PATH_PATTERNS = [
    (re.compile(r"(?i)(?<![A-Za-z0-9])[A-Z]:\\"), "Windows absolute path"),
    (
        re.compile(r"(?i)(?<![A-Za-z0-9)\]])" + re.escape(_HOME_PREFIX)),
        "home directory path",
    ),
    (
        re.compile(r"(?i)(?<![A-Za-z0-9)\]])" + re.escape(_USERS_PREFIX)),
        "Users directory path",
    ),
    (re.compile(r"(?i)(?:^|[^A-Za-z0-9])\\\\[A-Za-z0-9._-]+\\"), "UNC path"),
]

STANDARD_LIKE_PATTERNS = [
    re.compile(r"(?i)\b(?:ASME|ISO|API|GB/T|EN)\s*[-/]?\s*[0-9]{2,}\b"),
]


def _iter_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.parts)
    )


def _read_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _scan_text(label: str, text: str) -> list[str]:
    findings: list[str] = []
    for pattern, description in SECRET_PATTERNS + PATH_PATTERNS:
        if pattern.search(text):
            findings.append(f"{description} in {label}")
    for pattern in STANDARD_LIKE_PATTERNS:
        if pattern.search(text):
            findings.append(f"standard-like identifier in {label}")
    return findings


def audit_root(root: Path) -> list[str]:
    """Return generic findings for a working tree, including this audit script."""

    findings: list[str] = []
    for path in _iter_files(root):
        relative = path.relative_to(root).as_posix()
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            findings.append(f"blocked file type: {relative}")
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                findings.append(f"large artifact: {relative}")
        except OSError:
            findings.append(f"unreadable file metadata: {relative}")
        text = _read_text(path)
        if text is not None:
            findings.extend(_scan_text(relative, f"{relative}\n{text}"))
    return sorted(set(findings))


def main() -> int:
    findings = audit_root(ROOT)
    if findings:
        print("PUBLIC_RELEASE_AUDIT: FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("PUBLIC_RELEASE_AUDIT: PASS")
    print(f"SCANNED_TEXT_FILES={sum(_read_text(path) is not None for path in _iter_files(ROOT))}")
    print("NETWORK_ACCESS=NO")
    print("GENERIC_RULES_ONLY=YES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
