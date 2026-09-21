import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _audit_module():
    path = ROOT / "scripts" / "check_public_release.py"
    spec = importlib.util.spec_from_file_location("public_release_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generic_secret_marker_is_detected(tmp_path: Path) -> None:
    marker = "gh" + "p_" + "A" * 20
    (tmp_path / "sample.txt").write_text(marker, encoding="utf-8")

    findings = _audit_module().audit_root(tmp_path)

    assert any("GitHub token" in finding for finding in findings)


def test_windows_path_is_detected(tmp_path: Path) -> None:
    drive = "C" + ":\\"
    (tmp_path / "sample.txt").write_text(drive + "Users\\example", encoding="utf-8")

    findings = _audit_module().audit_root(tmp_path)

    assert any("Windows absolute path" in finding for finding in findings)


def test_home_path_is_detected(tmp_path: Path) -> None:
    home = "/" + "home/" + "example/secret.txt"
    (tmp_path / "sample.txt").write_text(home, encoding="utf-8")

    findings = _audit_module().audit_root(tmp_path)

    assert any("home directory path" in finding for finding in findings)


def test_standard_like_identifier_is_detected(tmp_path: Path) -> None:
    standard_like = "ASME" + " " + "1234"
    (tmp_path / "sample.txt").write_text(standard_like, encoding="utf-8")

    findings = _audit_module().audit_root(tmp_path)

    assert any("standard-like identifier" in finding for finding in findings)


def test_blocked_artifact_extension_is_detected(tmp_path: Path) -> None:
    suffix = "." + "pdf"
    (tmp_path / ("sample" + suffix)).write_bytes(b"synthetic placeholder")

    findings = _audit_module().audit_root(tmp_path)

    assert any("blocked file type" in finding for finding in findings)


def test_audit_script_is_scanned_and_current_tree_passes() -> None:
    module = _audit_module()

    assert not hasattr(module, "SELF")
    assert module.audit_root(module.ROOT) == []


def test_synthetic_phrases_and_plain_api_do_not_false_positive(tmp_path: Path) -> None:
    (tmp_path / "sample.txt").write_text(
        "RAG provenance engineering standards API synthetic data",
        encoding="utf-8",
    )

    assert _audit_module().audit_root(tmp_path) == []
