import hashlib
import os
from pathlib import Path

TRACKED_EXTENSIONS = {".go", ".py", ".ts", ".tsx", ".js", ".jsx"}


def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def compute_staleness_status(
    current_hash: str,
    stored_hash: str,
    days_since_indexed: float,
) -> str:
    if current_hash == stored_hash:
        return "fresh"
    if days_since_indexed > 7:
        return "confirmed_stale"
    return "potentially_stale"


def scan_workspace_files(workspace_path: str) -> list[dict]:
    results = []
    for root, dirs, files in os.walk(workspace_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("vendor", "node_modules", "__pycache__", ".venv")]
        for fname in files:
            if Path(fname).suffix in TRACKED_EXTENSIONS:
                full_path = os.path.join(root, fname)
                results.append({
                    "path": full_path,
                    "relative_path": os.path.relpath(full_path, workspace_path),
                    "hash": hash_file(full_path),
                    "language": "go" if fname.endswith(".go") else "python" if fname.endswith(".py") else "other",
                })
    return results
