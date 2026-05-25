#!/usr/bin/env python3
"""
mem-service — manage the agent-mem API server.

Commands:
    mem-service start   Check status; start if not running; register MCP + hooks
    mem-service stop    Stop the API server
    mem-service status  Show current status
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON  = PROJECT_DIR / ".venv" / "bin" / "python"
VENV_UVICORN = PROJECT_DIR / ".venv" / "bin" / "uvicorn"
PID_FILE     = Path("/tmp/agent-mem-api.pid")
LOG_FILE     = Path("/tmp/agent-mem-api.log")
API_URL      = "http://127.0.0.1:8000"
SETTINGS     = Path.home() / ".claude" / "settings.json"

HOOK_START = f"{VENV_PYTHON} {PROJECT_DIR}/hooks/session_start.py"
HOOK_STOP  = f"{VENV_PYTHON} {PROJECT_DIR}/hooks/session_end.py"


# ── helpers ──────────────────────────────────────────────────────────────────

def _pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (ProcessLookupError, ValueError, OSError):
        PID_FILE.unlink(missing_ok=True)
        return None


def _healthy() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(f"{API_URL}/workspaces", timeout=3)
        return True
    except Exception:
        return False


def _green(s): return f"\033[32m{s}\033[0m"
def _red(s):   return f"\033[31m{s}\033[0m"
def _dim(s):   return f"\033[2m{s}\033[0m"
def _bold(s):  return f"\033[1m{s}\033[0m"


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_status():
    pid = _pid()
    if pid:
        ok = _healthy()
        state = _green("running") if ok else _green("starting")
        print(f"  agent-mem   {state}   pid {pid}")
        print(f"  API         {API_URL}")
        print(f"  Logs        {LOG_FILE}")
    else:
        print(f"  agent-mem   {_red('stopped')}")


def cmd_start():
    pid = _pid()
    if pid and _healthy():
        print(_bold("agent-mem is already running"))
        cmd_status()
        return

    if not pid:
        print("Starting agent-mem API...", end=" ", flush=True)
        log = open(LOG_FILE, "a")
        proc = subprocess.Popen(
            [str(VENV_UVICORN), "api.main:app",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(PROJECT_DIR),
            env={**os.environ,
                 "HF_HOME": str(PROJECT_DIR / ".cache" / "models")},
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        log.close()
        PID_FILE.write_text(str(proc.pid))

        for _ in range(20):
            time.sleep(1)
            if _healthy():
                break
            print(".", end="", flush=True)
        print()

        if _healthy():
            print(_green(f"Started  (pid {proc.pid})"))
        else:
            print(f"Spawned (pid {proc.pid}) — API not ready yet, check {LOG_FILE}")

    _setup_mcp()
    _setup_hooks()
    print()
    cmd_status()


def cmd_stop():
    pid = _pid()
    if not pid:
        print("agent-mem is not running.")
        return
    try:
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)
        print(_green(f"Stopped  (pid {pid})"))
    except ProcessLookupError:
        PID_FILE.unlink(missing_ok=True)
        print("Process was already gone.")


# ── one-time setup ────────────────────────────────────────────────────────────

def _setup_mcp():
    claude = _find_claude()
    if not claude:
        print(_dim("  MCP       claude CLI not found — skipping"))
        return

    try:
        listed = subprocess.run(
            [claude, "mcp", "list"], capture_output=True, text=True, timeout=5
        )
        if "agent-mem" in listed.stdout:
            print(_dim("  MCP       already registered"))
            return
    except subprocess.TimeoutExpired:
        print(_dim("  MCP       timed out — skipping"))
        return

    try:
        subprocess.run(
            [claude, "mcp", "add", "--scope", "user",
             "agent-mem", str(VENV_PYTHON),
             str(PROJECT_DIR / "mcp" / "server.py")],
            check=True, capture_output=True, timeout=10,
        )
        print(_green("  MCP       registered agent-mem (user scope)"))
    except subprocess.CalledProcessError:
        print(f"  MCP       registration failed — run manually:")
        print(f"            claude mcp add --scope user agent-mem {VENV_PYTHON} {PROJECT_DIR}/mcp/server.py")


def _setup_hooks():
    if not SETTINGS.exists():
        print(_dim("  Hooks     ~/.claude/settings.json not found — skipping"))
        return

    try:
        settings = json.loads(SETTINGS.read_text())
    except json.JSONDecodeError:
        print("  Hooks     settings.json is not valid JSON — skipping")
        return

    existing_raw = json.dumps(settings.get("hooks", {}))
    if HOOK_START in existing_raw:
        print(_dim("  Hooks     already configured"))
        return

    settings.setdefault("hooks", {})
    settings["hooks"]["UserPromptSubmit"] = [
        {
            "matcher": ".*",
            "hooks": [{"type": "command", "command": HOOK_START}]
        }
    ]
    settings["hooks"]["Stop"] = [
        {
            "hooks": [{"type": "command", "command": HOOK_STOP}]
        }
    ]

    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
    print(_green("  Hooks     added to ~/.claude/settings.json"))


def _find_claude() -> str | None:
    for candidate in ["claude", "/opt/homebrew/bin/claude",
                       "/usr/local/bin/claude",
                       str(Path.home() / ".local/bin/claude")]:
        try:
            subprocess.run([candidate, "--version"],
                           capture_output=True, timeout=5)
            return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


# ── main ─────────────────────────────────────────────────────────────────────

COMMANDS = {"start": cmd_start, "stop": cmd_stop, "status": cmd_status}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: mem-service [{'|'.join(COMMANDS)}]")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
