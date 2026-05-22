#!/usr/bin/env python3
"""
UserPromptSubmit hook — fires on every message.
Only injects memory context on the FIRST message of a session (state file guard).
Outputs JSON that Claude Code injects as context before the user's message.
"""
import json
import os
import sys
import hashlib
import httpx
from pathlib import Path

API_URL = os.getenv("MEM_API_URL", "http://localhost:8000")
WORKSPACE_PATH = os.getcwd()
WORKSPACE_HASH = hashlib.md5(WORKSPACE_PATH.encode()).hexdigest()[:8]
STATE_FILE = Path(f"/tmp/mem-session-{WORKSPACE_HASH}.json")


def main():
    if STATE_FILE.exists():
        sys.exit(0)

    try:
        ws_resp = httpx.get(f"{API_URL}/workspaces", timeout=3).json()
        workspace = next((w for w in ws_resp if w["path"] == WORKSPACE_PATH), None)
        if not workspace:
            sys.exit(0)

        session_resp = httpx.post(
            f"{API_URL}/sessions",
            json={"workspace_id": workspace["id"]},
            timeout=3,
        ).json()
        session_id = session_resp["id"]

        context_resp = httpx.get(
            f"{API_URL}/context/{workspace['id']}",
            timeout=5,
        ).json()

        STATE_FILE.write_text(json.dumps({
            "session_id": session_id,
            "workspace_id": workspace["id"],
        }))

        lines = ["## Agent Memory — Session Context\n"]
        if context_resp.get("memories"):
            lines.append("### What I know about this workspace:\n")
            for m in context_resp["memories"]:
                lines.append(f"- **{m['title']}**: {m['content']}")

        if context_resp.get("stale_memories") or context_resp.get("stale_files"):
            lines.append("\n⚠️ **Stale memories detected — files changed since last index:**")
            for sf in context_resp.get("stale_files", []):
                lines.append(f"  - `{sf['path']}` ({sf['status']}, {sf['days_since_indexed']:.0f}d ago)")
            lines.append("\nRun `mem review` or ask me to re-index specific files.")

        if len(lines) > 1:
            output = {"context": "\n".join(lines)}
            print(json.dumps(output))

    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
