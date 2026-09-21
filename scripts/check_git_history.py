"""Scan reachable Git history for generic publication hazards."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_SIZE = 2_000_000
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


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def _scan_text(label: str, text: str) -> list[str]:
    findings: list[str] = []
    for pattern, description in SECRET_PATTERNS + PATH_PATTERNS:
        if pattern.search(text):
            findings.append(f"{description} in {label}")
    for pattern in STANDARD_LIKE_PATTERNS:
        if pattern.search(text):
            findings.append(f"standard-like identifier in {label}")
    return findings


def audit_history(root: Path) -> tuple[list[str], int]:
    """Return generic findings and the number of reachable blobs inspected."""

    findings: list[str] = []
    blobs: dict[str, list[str]] = {}
    for line in _git(root, "rev-list", "--objects", "--all").splitlines():
        fields = line.split(" ", 1)
        if len(fields) != 2:
            continue
        object_id, path = fields
        object_type = _git(root, "cat-file", "-t", object_id).strip()
        if object_type != "blob":
            continue
        blobs.setdefault(object_id, []).append(path)

    for object_id, paths in blobs.items():
        for path in paths:
            if Path(path).suffix.lower() in BLOCKED_SUFFIXES:
                findings.append(f"blocked file type in history: {path}")
        raw = subprocess.run(
            ["git", "cat-file", "-p", object_id],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
        if len(raw) > MAX_FILE_SIZE:
            findings.append(f"large historical blob: {object_id}")
        if b"\x00" in raw:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(_scan_text(f"history:{object_id}", text))
    return sorted(set(findings)), len(blobs)


def main() -> int:
    try:
        findings, blob_count = audit_history(ROOT)
    except subprocess.CalledProcessError as exc:
        print(f"GIT_HISTORY_AUDIT: ERROR ({exc})")
        return 1
    if findings:
        print("GIT_HISTORY_AUDIT: FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("GIT_HISTORY_AUDIT: PASS")
    print(f"REACHABLE_BLOBS={blob_count}")
    print("GENERIC_RULES_ONLY=YES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
