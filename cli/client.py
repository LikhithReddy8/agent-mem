import httpx
from api.config import settings


class MemClient:
    def __init__(self, base_url: str = settings.mem_api_url):
        self._base = base_url

    def _c(self) -> httpx.Client:
        return httpx.Client(base_url=self._base, timeout=15)

    def search(self, query: str, workspace_id: str | None = None, limit: int = 10) -> dict:
        payload: dict = {"query": query, "limit": limit}
        if workspace_id:
            payload["workspace_id"] = workspace_id
        with self._c() as c:
            return c.post("/search", json=payload).json()

    def list_memories(self, workspace_id: str | None = None) -> list:
        with self._c() as c:
            resp = c.get(f"/status/{workspace_id}" if workspace_id else "/memories")
            data = resp.json()
            return data.get("memories", data) if isinstance(data, dict) else data

    def add_memory(self, workspace_id: str, title: str, content: str, type: str = "decision", importance: float = 0.9) -> dict:
        with self._c() as c:
            return c.post("/memories", json={
                "type": type, "workspace_id": workspace_id,
                "title": title, "content": content, "importance_score": importance,
            }).json()

    def delete_memory(self, memory_id: str) -> bool:
        with self._c() as c:
            return c.delete(f"/memories/{memory_id}").status_code == 204

    def validate_memory(self, memory_id: str) -> dict:
        with self._c() as c:
            return c.patch(f"/memories/{memory_id}/validate").json()

    def get_status(self, workspace_id: str) -> dict:
        with self._c() as c:
            return c.get(f"/status/{workspace_id}").json()

    def list_workspaces(self) -> list:
        with self._c() as c:
            return c.get("/workspaces").json()

    def add_workspace(self, name: str, path: str, language: str | None = None) -> dict:
        with self._c() as c:
            return c.post("/workspaces", json={"name": name, "path": path, "language": language}).json()

    def delete_workspace(self, workspace_id: str) -> bool:
        with self._c() as c:
            return c.delete(f"/workspaces/{workspace_id}").status_code == 204

    def list_sessions(self, workspace_id: str | None = None) -> list:
        with self._c() as c:
            params = {"workspace_id": workspace_id} if workspace_id else {}
            return c.get("/sessions", params=params).json()

    def get_context(self, workspace_id: str) -> dict:
        with self._c() as c:
            return c.get(f"/context/{workspace_id}").json()
