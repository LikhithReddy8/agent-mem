"""
MCP server for agent-mem.

The local `mcp/` package shadows the installed `mcp` library.  The package
__init__.py pre-registers the library's submodules in sys.modules so the
imports below resolve to the installed package, not this file.
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from .tools import memory_search, memory_save, memory_get_context, memory_validate, memory_flag_stale

server = Server("agent-mem")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="memory_search",
            description="Semantic search across stored memories. Call this when you need context about a specific topic, file, or past decision.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "workspace": {"type": "string", "description": "Workspace ID to scope search (optional)"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="memory_save",
            description="Save a memory — decision, code knowledge, or session summary. Use this to persist important context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "type": {"type": "string", "enum": ["decision", "code_knowledge", "session_summary"]},
                    "workspace": {"type": "string", "description": "Workspace ID"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "metadata": {"type": "object"},
                },
                "required": ["title", "content", "type", "workspace"],
            },
        ),
        types.Tool(
            name="memory_get_context",
            description="Get the top memories for a workspace, sorted by importance. Called at session start to load context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace": {"type": "string", "description": "Workspace ID"},
                },
                "required": ["workspace"],
            },
        ),
        types.Tool(
            name="memory_validate",
            description="Mark a memory as still accurate after you've verified the current code matches it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                },
                "required": ["memory_id"],
            },
        ),
        types.Tool(
            name="memory_flag_stale",
            description="Flag a memory as outdated after you've read the current code and found it differs from the stored memory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "reason": {"type": "string", "description": "What changed"},
                },
                "required": ["memory_id", "reason"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "memory_search":
        result = memory_search(**arguments)
    elif name == "memory_save":
        result = memory_save(**arguments)
    elif name == "memory_get_context":
        result = memory_get_context(arguments["workspace"])
    elif name == "memory_validate":
        result = memory_validate(arguments["memory_id"])
    elif name == "memory_flag_stale":
        result = memory_flag_stale(arguments["memory_id"], arguments["reason"])
    else:
        result = {"error": f"Unknown tool: {name}"}
    import json
    return [types.TextContent(type="text", text=json.dumps(result, default=str))]


async def main():
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
