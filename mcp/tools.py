import httpx
from api.config import settings

BASE = settings.mem_api_url


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE, timeout=10)


def memory_search(query: str, workspace: str | None = None, limit: int = 5) -> dict:
    payload: dict = {"query": query, "limit": limit}
    if workspace:
        payload["workspace_id"] = workspace
    with _client() as c:
        return c.post("/search", json=payload).json()


def memory_save(
    title: str,
    content: str,
    type: str,
    workspace: str,
    tags: list[str] = [],
    metadata: dict = {},
) -> dict:
    with _client() as c:
        return c.post("/memories", json={
            "type": type,
            "workspace_id": workspace,
            "title": title,
            "content": content,
            "tags": tags,
            "metadata": metadata,
        }).json()


def memory_get_context(workspace: str) -> dict:
    with _client() as c:
        return c.get(f"/context/{workspace}").json()


def memory_validate(memory_id: str) -> dict:
    with _client() as c:
        return c.patch(f"/memories/{memory_id}/validate").json()


def memory_flag_stale(memory_id: str, reason: str) -> dict:
    with _client() as c:
        resp = c.patch(f"/memories/{memory_id}/flag-stale", json={"reason": reason})
        return resp.json()
