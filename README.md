# agent-mem

Persistent memory backend for Claude Code. Survives session restarts, works across multiple workspaces, and injects relevant context automatically at the start of every conversation.

## The problem it solves

- Claude forgets everything when you close a terminal
- You re-explain the same architecture every session
- No way to share learnings across projects or ask questions across conversations
- Code indexing has to be redone each time

## How it works

```
Claude Code session starts
       │
       ▼
session_start hook fires
       │
  finds your workspace by cwd path
       │
  fetches relevant memories (semantic search)
       │
  injects context into the conversation
       │
       ▼
You work with Claude — it already knows the codebase
       │
       ▼
session_end hook fires → session marked closed
```

Memories are stored in PostgreSQL with pgvector. Semantic search uses `all-mpnet-base-v2` (768-dim embeddings, HNSW index) running locally — no API key required.

---

## Stack

| Layer | Tech |
|-------|------|
| API | FastAPI + uvicorn |
| DB | PostgreSQL 17 + pgvector 0.8.2 |
| Embeddings | sentence-transformers `all-mpnet-base-v2` (local) |
| MCP | `mcp` library, 5 tools |
| CLI | Typer + Rich |
| ORM | SQLAlchemy 2 async + asyncpg |
| Migrations | Alembic |

---

## Installation

**Requirements:** Python 3.13+, PostgreSQL 17 with pgvector extension

```bash
git clone git@github.com:LikhithReddy8/agent-mem.git
cd agent-mem

python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Copy and configure environment:
```bash
cp .env.example .env
# edit .env — set DATABASE_URL to your postgres instance
```

Run migrations:
```bash
alembic upgrade head
```

Make CLIs globally accessible:
```bash
ln -sf "$(pwd)/.venv/bin/mem" /opt/homebrew/bin/mem
ln -sf "$(pwd)/.venv/bin/mem-service" /opt/homebrew/bin/mem-service
```

---

## Starting the service

```bash
mem-service start
```

This will:
1. Start the API server (port 8000) as a background process
2. Register the MCP server with Claude Code (`claude mcp add --scope user`)
3. Add session hooks to `~/.claude/settings.json`

```bash
mem-service stop     # stop the API server
mem-service status   # show status + registered workspaces
```

---

## Workspace management

A workspace is a registered project directory. Claude Code sessions are scoped to a workspace based on the current working directory.

```bash
# Register a single workspace
mem workspace add my-service /path/to/my-service

# Bulk-register all subdirectories (git repos only by default)
mem workspace init                    # scans current directory
mem workspace init /path/to/projects  # scans a specific folder
mem workspace init --all              # include non-git directories

# List all workspaces
mem workspace list

# Delete a workspace and all its memories
mem workspace delete <id>             # first 8 chars of ID work
mem workspace delete <id> --yes       # skip confirmation
```

---

## Memory management

```bash
# Search memories
mem search "how does the auth flow work"
mem search "database schema" --workspace <id>

# Add a memory manually
mem memory add <workspace-id> "Auth uses JWT with 1h expiry" --type decision

# List memories for a workspace
mem memory list --workspace <id>

# Delete a memory
mem memory delete <memory-id>

# Validate a memory (mark as confirmed accurate)
mem memory validate <memory-id>
```

---

## MCP tools (Claude Code integration)

Once `mem-service start` is run, Claude Code has 5 tools available:

| Tool | What it does |
|------|-------------|
| `memory_search` | Semantic search across stored memories |
| `memory_save` | Store a new memory with embedding |
| `memory_get_context` | Fetch full context for a workspace |
| `memory_validate` | Mark a memory as validated |
| `memory_flag_stale` | Flag a memory as outdated |

---

## Session hooks

Hooks fire automatically via Claude Code's hook system:

- **`UserPromptSubmit`** (`hooks/session_start.py`) — on first prompt of a session, finds the workspace matching cwd, creates a session record, fetches relevant memories, and prints context JSON for Claude
- **`Stop`** (`hooks/session_end.py`) — marks the session as closed when Claude Code exits

State is tracked in `/tmp/mem-session-<hash>.json` to prevent duplicate injections within a session.

---

## REST API

The API runs at `http://127.0.0.1:8000`. Full OpenAPI docs at `/docs`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workspaces` | Create workspace |
| GET | `/workspaces` | List workspaces |
| DELETE | `/workspaces/{id}` | Delete workspace + all memories |
| POST | `/sessions` | Create session |
| GET | `/sessions` | List sessions |
| PATCH | `/sessions/{id}` | Update session |
| POST | `/memories` | Store memory (auto-embeds) |
| GET | `/memories/{id}` | Get memory |
| DELETE | `/memories/{id}` | Delete memory |
| PATCH | `/memories/{id}/validate` | Validate memory |
| PATCH | `/memories/{id}/flag-stale` | Flag as stale |
| POST | `/search` | Semantic search |
| GET | `/context/{workspace_id}` | Full workspace context |
| POST | `/reindex` | Re-embed all memories |
| GET | `/status/{workspace_id}` | Workspace stats |

---

## Project structure

```
agent-mem/
├── api/
│   ├── config.py          # Settings (DATABASE_URL, etc.)
│   ├── db.py              # Async SQLAlchemy engine + session
│   ├── embeddings.py      # all-mpnet-base-v2 singleton
│   ├── models.py          # ORM: Workspace, Session, Memory, FileIndex
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── staleness.py       # SHA256 file hashing for staleness detection
│   └── routers/
│       ├── workspaces.py  # /workspaces endpoints
│       ├── sessions.py    # /sessions endpoints
│       ├── memories.py    # /memories endpoints
│       └── search.py      # /search, /context, /reindex, /status
├── cli/
│   ├── client.py          # MemClient — typed httpx wrapper
│   ├── main.py            # Typer app root
│   └── commands/
│       ├── workspaces.py  # mem workspace add/init/list/delete
│       ├── memories.py    # mem memory add/list/delete/validate
│       ├── search.py      # mem search
│       ├── sessions.py    # mem sessions
│       ├── status.py      # mem status
│       ├── review.py      # mem review
│       └── reindex.py     # mem reindex
├── mcp/
│   ├── server.py          # MCP server entry point
│   └── tools.py           # 5 MCP tool implementations
├── hooks/
│   ├── session_start.py   # UserPromptSubmit hook
│   └── session_end.py     # Stop hook
├── migrations/            # Alembic migrations
├── mem_service.py         # mem-service CLI (start/stop/status)
├── docker-compose.yml     # PostgreSQL + pgvector via Docker
└── pyproject.toml
```

---

## Docker (database only)

If you don't have PostgreSQL locally, spin up just the database:

```bash
docker compose up -d db
```

Then set `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_mem` in `.env`.

---

## Development

```bash
# Run tests
pytest

# Run API in dev mode (auto-reload)
.venv/bin/uvicorn api.main:app --reload
```

Tests use a real PostgreSQL database (no mocks) with per-test rollback for isolation.

---

## Recent changes

- **Workspace delete** — `mem workspace delete <id>` removes a workspace and all associated memories, file indexes, and sessions in correct FK order
- **Workspace init** — `mem workspace init` bulk-registers all subdirectories; defaults to current directory when no path given; auto-detects language (Go, Python, JavaScript, Rust); skips already-registered paths
- **Workspace list in status** — `mem-service status` shows a formatted table of all registered workspaces
- **mem-service** — single script to start/stop the API, register MCP, and configure hooks; `stop` now kills all processes on port 8000 (not just the tracked PID) to prevent stale server issues
- **Session hooks** — automatic context injection on session start; state file guard prevents duplicate injection within a session
