#!/usr/bin/env python3
"""
Stop hook — fires when Claude Code session ends (or on SIGTERM/crash).
Closes the session record and removes the state file.
"""
import json
import os
import sys
import signal
import hashlib
import httpx
from pathlib import Path

API_URL = os.getenv("MEM_API_URL", "http://localhost:8000")
WORKSPACE_PATH = os.getcwd()
WORKSPACE_HASH = hashlib.md5(WORKSPACE_PATH.encode()).hexdigest()[:8]
STATE_FILE = Path(f"/tmp/mem-session-{WORKSPACE_HASH}.json")


def close_session(signum=None, frame=None):
    if not STATE_FILE.exists():
        sys.exit(0)
    try:
        state = json.loads(STATE_FILE.read_text())
        session_id = state.get("session_id")
        if session_id:
            from datetime import datetime, timezone
            httpx.patch(
                f"{API_URL}/sessions/{session_id}",
                json={
                    "status": "closed",
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                },
                timeout=3,
            )
    except Exception:
        pass
    finally:
        STATE_FILE.unlink(missing_ok=True)
        sys.exit(0)


signal.signal(signal.SIGTERM, close_session)

if __name__ == "__main__":
    close_session()
