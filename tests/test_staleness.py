import hashlib
from api.staleness import hash_file, compute_staleness_status, scan_workspace_files


def test_hash_file_returns_sha256(tmp_path):
    f = tmp_path / "test.go"
    f.write_text("package main\nfunc main() {}")
    result = hash_file(str(f))
    expected = hashlib.sha256(b"package main\nfunc main() {}").hexdigest()
    assert result == expected


def test_hash_file_changes_when_content_changes(tmp_path):
    f = tmp_path / "test.go"
    f.write_text("version 1")
    h1 = hash_file(str(f))
    f.write_text("version 2")
    h2 = hash_file(str(f))
    assert h1 != h2


def test_compute_staleness_status_fresh_when_hash_matches():
    status = compute_staleness_status(
        current_hash="abc123",
        stored_hash="abc123",
        days_since_indexed=0,
    )
    assert status == "fresh"


def test_compute_staleness_status_potentially_stale_recent():
    status = compute_staleness_status(
        current_hash="new_hash",
        stored_hash="old_hash",
        days_since_indexed=0.5,
    )
    assert status == "potentially_stale"


def test_compute_staleness_status_confirmed_stale_old():
    status = compute_staleness_status(
        current_hash="new_hash",
        stored_hash="old_hash",
        days_since_indexed=10,
    )
    assert status == "confirmed_stale"


def test_scan_workspace_files_finds_go_and_python(tmp_path):
    (tmp_path / "main.go").write_text("package main")
    (tmp_path / "handler.py").write_text("def handle(): pass")
    (tmp_path / "README.md").write_text("# docs")
    results = scan_workspace_files(str(tmp_path))
    paths = [r["path"] for r in results]
    assert any("main.go" in p for p in paths)
    assert any("handler.py" in p for p in paths)
    assert not any("README.md" in p for p in paths)
