# tests/test_api_search.py
import pytest


@pytest.fixture
async def seeded(client):
    ws = (await client.post("/workspaces", json={"name": "search-ws", "path": "/tmp/search-ws"})).json()
    await client.post("/memories", json={
        "type": "decision",
        "workspace_id": ws["id"],
        "title": "Use UUIDs not integer IDs",
        "content": "All primary keys are UUID for portability.",
        "importance_score": 0.9,
        "tags": ["schema", "ids"],
    })
    await client.post("/memories", json={
        "type": "code_knowledge",
        "workspace_id": ws["id"],
        "title": "JWT token refresh flow",
        "content": "Auth middleware uses sliding window token refresh with mutex protection.",
        "importance_score": 0.7,
        "tags": ["auth", "jwt"],
    })
    await client.post("/memories", json={
        "type": "session_summary",
        "workspace_id": ws["id"],
        "title": "Payment webhook debugging session",
        "content": "Fixed retry logic for failed Stripe webhooks using exponential backoff.",
        "importance_score": 0.5,
        "tags": ["payment", "webhooks"],
    })
    return ws


async def test_search_returns_relevant_memory(client, seeded):
    resp = await client.post("/search", json={"query": "JWT token refresh race condition", "limit": 3})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0
    titles = [r["memory"]["title"] for r in results]
    assert "JWT token refresh flow" in titles


async def test_search_scoped_to_workspace(client, seeded):
    other_ws = (await client.post("/workspaces", json={"name": "other", "path": "/tmp/other-ws"})).json()
    resp = await client.post("/search", json={
        "query": "JWT token",
        "workspace_id": other_ws["id"],
        "limit": 5,
    })
    assert resp.status_code == 200
    assert resp.json()["results"] == []


async def test_get_context_returns_memories_sorted_by_importance(client, seeded):
    resp = await client.get(f"/context/{seeded['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["memories"]) > 0
    scores = [m["importance_score"] for m in data["memories"]]
    assert scores == sorted(scores, reverse=True)


async def test_get_status_counts_by_staleness(client, seeded):
    resp = await client.get(f"/status/{seeded['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["fresh"] == 3
    assert data["potentially_stale"] == 0
    assert data["confirmed_stale"] == 0
