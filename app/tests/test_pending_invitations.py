import pytest


async def register_and_login(client, email: str, first: str = "A", last: str = "B"):
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
    return response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


async def user_id_from_me(client, token: str) -> str:
    r = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert r.status_code == 200
    return r.json()["id"]


@pytest.mark.asyncio
async def test_list_pending_invitations_and_accept(client):
    token_owner = await register_and_login(client, "own-inv@example.com", "Own", "Er")
    token_member = await register_and_login(client, "mem-inv@example.com", "Mem", "Ber")
    uid_member = await user_id_from_me(client, token_member)

    r = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token_owner),
        json={"name": "Invite Project", "status": "pending"},
    )
    assert r.status_code == 201
    project_id = r.json()["id"]

    r = await client.post(
        f"/api/v1/projects/{project_id}/invitations",
        headers=auth_headers(token_owner),
        json={"user_id": uid_member, "role": "member"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "pending"

    # Invitee sees pending invitation
    r = await client.get("/api/v1/me/invitations", headers=auth_headers(token_member))
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    inv = data["items"][0]
    assert inv["status"] == "pending"
    assert inv["project_id"] == project_id
    assert inv["project_name"] == "Invite Project"
    assert inv["role"] == "member"
    assert inv["invited_by_first_name"] == "Own"

    # Owner does not see it in their pending list
    r = await client.get("/api/v1/me/invitations", headers=auth_headers(token_owner))
    assert r.status_code == 200
    assert r.json()["total"] == 0

    # Accept
    r = await client.post(
        f"/api/v1/projects/{project_id}/invitations/accept",
        headers=auth_headers(token_member),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "active"

    # Pending list empty after accept
    r = await client.get("/api/v1/me/invitations", headers=auth_headers(token_member))
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_pending_invitations_unauthenticated(client):
    r = await client.get("/api/v1/me/invitations")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_reject_clears_pending_list(client):
    token_owner = await register_and_login(client, "own-rej@example.com", "O", "R")
    token_member = await register_and_login(client, "mem-rej@example.com", "M", "R")
    uid_member = await user_id_from_me(client, token_member)

    r = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token_owner),
        json={"name": "Reject Project", "status": "pending"},
    )
    project_id = r.json()["id"]
    await client.post(
        f"/api/v1/projects/{project_id}/invitations",
        headers=auth_headers(token_owner),
        json={"user_id": uid_member, "role": "member"},
    )

    r = await client.post(
        f"/api/v1/projects/{project_id}/invitations/reject",
        headers=auth_headers(token_member),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"

    r = await client.get("/api/v1/me/invitations", headers=auth_headers(token_member))
    assert r.status_code == 200
    assert r.json()["total"] == 0
