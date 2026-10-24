import pytest


async def register_and_login(client, email: str, first="Test", last="User"):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123",
            "first_name": first,
            "last_name": last,
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"], data.get("user", {}).get("id") or None


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


async def get_user_id(client, token: str):
    r = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={"name": "Temp", "status": "pending"},
    )
    assert r.status_code == 201
    return r.json()["user_id"]


@pytest.mark.asyncio
async def test_invite_accept_flow(client):
    token_a, _ = await register_and_login(client, "owner@collab.com", "Owner", "A")
    token_b, _ = await register_and_login(client, "member@collab.com", "Member", "B")
    uid_a = await get_user_id(client, token_a)
    uid_b = await get_user_id(client, token_b)
    r = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token_a),
        json={"name": "Shared Project", "status": "pending"},
    )
    assert r.status_code == 201
    project_id = r.json()["id"]
    r = await client.get(f"/api/v1/users/{uid_b}/public", headers=auth_headers(token_a))
    assert r.status_code == 200
    assert r.json()["first_name"] == "Member"
    assert "email" not in r.json()
    r = await client.post(
        f"/api/v1/projects/{project_id}/invitations",
        headers=auth_headers(token_a),
        json={"user_id": uid_b, "role": "member"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "pending"
    r = await client.post(
        f"/api/v1/projects/{project_id}/invitations",
        headers=auth_headers(token_a),
        json={"user_id": uid_b, "role": "member"},
    )
    assert r.status_code == 409
    r = await client.post(
        f"/api/v1/projects/{project_id}/invitations/accept",
        headers=auth_headers(token_b),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "active"
    r = await client.get("/api/v1/projects", headers=auth_headers(token_b))
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()["items"]]
    assert project_id in ids
    r = await client.get(
        f"/api/v1/projects/{project_id}/members",
        headers=auth_headers(token_b),
    )
    assert r.status_code == 200
    assert r.json()["total"] >= 2


@pytest.mark.asyncio
async def test_cannot_assign_non_member(client):
    token_a, _ = await register_and_login(client, "owner2@collab.com")
    token_b, _ = await register_and_login(client, "outsider@collab.com")
    uid_a = await get_user_id(client, token_a)
    uid_b = await get_user_id(client, token_b)
    r = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token_a),
        json={"name": "Solo", "status": "pending"},
    )
    project_id = r.json()["id"]
    r = await client.post(
        "/api/v1/tasks",
        headers=auth_headers(token_a),
        json={"project_id": project_id, "title": "Task", "assignee_id": uid_b},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_cross_project_access_denied(client):
    token_a, _ = await register_and_login(client, "a3@collab.com")
    token_b, _ = await register_and_login(client, "b3@collab.com")
    r = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token_a),
        json={"name": "Private", "status": "pending"},
    )
    project_id = r.json()["id"]
    r = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(token_b),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_self_invite_rejected(client):
    token, _ = await register_and_login(client, "self@collab.com")
    uid = await get_user_id(client, token)
    r = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={"name": "P", "status": "pending"},
    )
    project_id = r.json()["id"]
    r = await client.post(
        f"/api/v1/projects/{project_id}/invitations",
        headers=auth_headers(token),
        json={"user_id": uid, "role": "member"},
    )
    assert r.status_code == 400
