import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _history_module():
    path = ROOT / "scripts" / "check_git_history.py"
    spec = importlib.util.spec_from_file_location("git_history_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_reachable_history_passes_generic_audit() -> None:
    findings, blob_count = _history_module().audit_history(ROOT)

    assert findings == []
    assert blob_count > 0


def test_history_audit_detects_secret_in_local_test_repository(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Synthetic Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "synthetic@example.invalid"], cwd=tmp_path, check=True)
    marker = "gh" + "p_" + "A" * 20
    (tmp_path / "sample.txt").write_text(marker, encoding="utf-8")
    subprocess.run(["git", "add", "sample.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "synthetic audit fixture"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    findings, _ = _history_module().audit_history(tmp_path)

    assert any("secret-like" in finding or "GitHub token" in finding for finding in findings)
