import pytest


async def register_and_login(client, email: str):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_client(client):
    token = await register_and_login(
        client,
        "client-create@example.com",
    )

    response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "Ali Ahmadi",
            "company": "Ahmadi Design",
            "email": "ali@example.com",
            "phone": "+989121234567",
            "address": "Tehran",
            "notes": "Important client",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Ali Ahmadi"
    assert data["company"] == "Ahmadi Design"
    assert data["email"] == "ali@example.com"
    assert data["phone"] == "+989121234567"
    assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_list_clients(client):
    token = await register_and_login(
        client,
        "client-list@example.com",
    )

    for name in ["Ali Ahmadi", "Sara Karimi"]:
        response = await client.post(
            "/api/v1/clients",
            headers=auth_headers(token),
            json={
                "name": name,
            },
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/v1/clients",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_client(client):
    token = await register_and_login(
        client,
        "client-get@example.com",
    )

    create_response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "Get Client",
        },
    )

    assert create_response.status_code == 201

    client_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == client_id
    assert response.json()["name"] == "Get Client"


@pytest.mark.asyncio
async def test_update_client(client):
    token = await register_and_login(
        client,
        "client-update@example.com",
    )

    create_response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "Old Client Name",
            "company": "Old Company",
        },
    )

    assert create_response.status_code == 201

    client_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(token),
        json={
            "name": "New Client Name",
            "company": "New Company",
            "phone": "+989120000000",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Client Name"
    assert data["company"] == "New Company"
    assert data["phone"] == "+989120000000"


@pytest.mark.asyncio
async def test_delete_client(client):
    token = await register_and_login(
        client,
        "client-delete@example.com",
    )

    create_response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "Delete Client",
        },
    )

    assert create_response.status_code == 201

    client_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    get_response = await client.get(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_client_search_by_name(client):
    token = await register_and_login(
        client,
        "client-search@example.com",
    )

    await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "Ali Ahmadi",
        },
    )

    await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "Sara Karimi",
        },
    )

    response = await client.get(
        "/api/v1/clients",
        headers=auth_headers(token),
        params={
            "search": "Ali",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Ali Ahmadi"


@pytest.mark.asyncio
async def test_client_pagination(client):
    token = await register_and_login(
        client,
        "client-pagination@example.com",
    )

    for i in range(5):
        response = await client.post(
            "/api/v1/clients",
            headers=auth_headers(token),
            json={
                "name": f"Client {i}",
            },
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/v1/clients",
        headers=auth_headers(token),
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_client_ownership(client):
    user_a_token = await register_and_login(
        client,
        "client-user-a@example.com",
    )

    user_b_token = await register_and_login(
        client,
        "client-user-b@example.com",
    )

    create_response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(user_a_token),
        json={
            "name": "Private Client A",
        },
    )

    assert create_response.status_code == 201

    client_id = create_response.json()["id"]

    # User B cannot read User A's client.
    response = await client.get(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(user_b_token),
    )

    assert response.status_code == 404

    # User B cannot update User A's client.
    response = await client.patch(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(user_b_token),
        json={
            "name": "Hacked Client",
        },
    )

    assert response.status_code == 404

    # User B cannot delete User A's client.
    response = await client.delete(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(user_b_token),
    )

    assert response.status_code == 404

    # User A's client must still exist.
    response = await client.get(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(user_a_token),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Private Client A"
