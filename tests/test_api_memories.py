# tests/test_api_memories.py
import pytest
import uuid


@pytest.fixture
async def workspace(client):
    resp = await client.post("/workspaces", json={"name": "mem-ws", "path": "/tmp/test-ws-memories"})
    return resp.json()


async def test_create_memory_generates_embedding(client, workspace):
    resp = await client.post("/memories", json={
        "type": "decision",
        "workspace_id": workspace["id"],
        "title": "Use UUIDs not integer IDs",
        "content": "All tables use UUID primary keys for portability and security.",
        "importance_score": 0.9,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Use UUIDs not integer IDs"
    assert data["staleness_status"] == "fresh"
    assert "id" in data


async def test_get_memory(client, workspace):
    created = (await client.post("/memories", json={
        "type": "code_knowledge",
        "workspace_id": workspace["id"],
        "title": "Auth flow",
        "content": "JWT sliding window token refresh.",
    })).json()
    resp = await client.get(f"/memories/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_delete_memory(client, workspace):
    created = (await client.post("/memories", json={
        "type": "session_summary",
        "workspace_id": workspace["id"],
        "title": "Session recap",
        "content": "Fixed payment webhook retry.",
    })).json()
    del_resp = await client.delete(f"/memories/{created['id']}")
    assert del_resp.status_code == 204
    get_resp = await client.get(f"/memories/{created['id']}")
    assert get_resp.status_code == 404


async def test_validate_memory_resets_staleness(client, workspace):
    created = (await client.post("/memories", json={
        "type": "code_knowledge",
        "workspace_id": workspace["id"],
        "title": "Payment flow",
        "content": "API gateway → payment-service → stripe-adapter.",
    })).json()
    resp = await client.patch(f"/memories/{created['id']}/validate")
    assert resp.status_code == 200
    assert resp.json()["staleness_status"] == "fresh"
    assert resp.json()["last_validated_at"] is not None


async def test_flag_stale_memory(client, workspace):
    created = (await client.post("/memories", json={
        "type": "code_knowledge",
        "workspace_id": workspace["id"],
        "title": "Old auth flow",
        "content": "Auth uses basic tokens.",
    })).json()
    resp = await client.patch(f"/memories/{created['id']}/flag-stale", json={"reason": "Switched to JWT"})
    assert resp.status_code == 200
    assert resp.json()["staleness_status"] == "confirmed_stale"
