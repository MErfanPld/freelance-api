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
    data = response.json()
    return data["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_my_public_id_authenticated(client):
    token = await register_and_login(client, "publicid@example.com", "Pub", "User")
    # Resolve expected id via /auth/me
    me = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    expected_id = me.json()["id"]

    r = await client.get("/api/v1/users/me/public-id", headers=auth_headers(token))
    assert r.status_code == 200
    body = r.json()
    assert body == {"id": expected_id}
    assert set(body.keys()) == {"id"}
    assert "email" not in body
    assert "password" not in body
    assert "password_hash" not in str(body).lower()
    assert "token" not in str(body).lower()


@pytest.mark.asyncio
async def test_public_id_matches_database_user(client):
    token = await register_and_login(client, "match@example.com")
    me = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    expected = me.json()["id"]
    r = await client.get("/api/v1/users/me/public-id", headers=auth_headers(token))
    assert r.status_code == 200
    assert r.json()["id"] == expected


@pytest.mark.asyncio
async def test_public_id_unauthenticated_401(client):
    r = await client.get("/api/v1/users/me/public-id")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_public_id_invalid_token_401(client):
    r = await client.get(
        "/api/v1/users/me/public-id",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_public_id_cannot_select_other_user(client):
    token_a = await register_and_login(client, "owner-a@example.com", "A", "One")
    token_b = await register_and_login(client, "member-b@example.com", "B", "Two")
    me_a = await client.get("/api/v1/auth/me", headers=auth_headers(token_a))
    me_b = await client.get("/api/v1/auth/me", headers=auth_headers(token_b))
    id_a = me_a.json()["id"]
    id_b = me_b.json()["id"]
    assert id_a != id_b

    # Path is fixed to /me — no way to pass another user's id
    r = await client.get("/api/v1/users/me/public-id", headers=auth_headers(token_a))
    assert r.status_code == 200
    assert r.json()["id"] == id_a
    assert r.json()["id"] != id_b

    r = await client.get("/api/v1/users/me/public-id", headers=auth_headers(token_b))
    assert r.status_code == 200
    assert r.json()["id"] == id_b
