import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "StrongPassword123",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"

    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123",
        "first_name": "Test",
        "last_name": "User",
    }

    first_response = await client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert second_response.status_code in {400, 409}


@pytest.mark.asyncio
async def test_login(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123",
            "first_name": "Login",
            "last_name": "User",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "StrongPassword123",
            "first_name": "Wrong",
            "last_name": "Password",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "StrongPassword123",
            "first_name": "Me",
            "last_name": "User",
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "me@example.com",
            "password": "StrongPassword123",
        },
    )

    access_token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_without_token(client):
    response = await client.get(
        "/api/v1/auth/me",
    )

    assert response.status_code == 401