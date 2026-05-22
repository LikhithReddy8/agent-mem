# tests/test_api_workspaces.py
import pytest


async def test_create_workspace(client):
    resp = await client.post("/workspaces", json={
        "name": "auth-service",
        "path": "/projects/auth-service",
        "language": "go",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "auth-service"
    assert data["path"] == "/projects/auth-service"
    assert data["language"] == "go"
    assert "id" in data


async def test_create_workspace_duplicate_path_returns_409(client):
    payload = {"name": "svc", "path": "/projects/unique-svc"}
    await client.post("/workspaces", json=payload)
    resp = await client.post("/workspaces", json=payload)
    assert resp.status_code == 409


async def test_list_workspaces(client):
    await client.post("/workspaces", json={"name": "svc-a", "path": "/projects/svc-a"})
    await client.post("/workspaces", json={"name": "svc-b", "path": "/projects/svc-b"})
    resp = await client.get("/workspaces")
    assert resp.status_code == 200
    names = [w["name"] for w in resp.json()]
    assert "svc-a" in names
    assert "svc-b" in names
