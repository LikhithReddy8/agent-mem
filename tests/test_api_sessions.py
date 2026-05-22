# tests/test_api_sessions.py
import pytest
from datetime import datetime, timezone


@pytest.fixture
async def workspace(client):
    resp = await client.post("/workspaces", json={"name": "test-ws", "path": "/tmp/test-ws-sessions"})
    return resp.json()


async def test_create_session(client, workspace):
    resp = await client.post("/sessions", json={"workspace_id": workspace["id"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["workspace_id"] == workspace["id"]
    assert data["status"] == "active"
    assert data["ended_at"] is None


async def test_get_session(client, workspace):
    created = (await client.post("/sessions", json={"workspace_id": workspace["id"]})).json()
    resp = await client.get(f"/sessions/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_patch_session_closes_it(client, workspace):
    created = (await client.post("/sessions", json={"workspace_id": workspace["id"]})).json()
    resp = await client.patch(f"/sessions/{created['id']}", json={
        "status": "closed",
        "summary": "Debugged token refresh race condition.",
        "ended_at": datetime.now(timezone.utc).isoformat(),
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "closed"
    assert data["summary"] == "Debugged token refresh race condition."
    assert data["ended_at"] is not None


async def test_get_session_not_found(client):
    import uuid
    resp = await client.get(f"/sessions/{uuid.uuid4()}")
    assert resp.status_code == 404
