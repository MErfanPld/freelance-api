import pytest


async def register_and_login(
    client,
    email: str,
):
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
    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.mark.asyncio
async def test_create_project(client):
    token = await register_and_login(
        client,
        "project@example.com",
    )

    response = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "Website Project",
            "description": "Build a company website",
            "status": "pending",
            "priority": "high",
            "budget": "1500.00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Website Project"
    assert data["description"] == "Build a company website"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert data["budget"] == "1500.00"
    assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_list_projects(client):
    token = await register_and_login(
        client,
        "list@example.com",
    )

    for name in ["Project One", "Project Two"]:
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers(token),
            json={
                "name": name,
            },
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/v1/projects",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_project(client):
    token = await register_and_login(
        client,
        "get-project@example.com",
    )

    create_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "Get Project",
        },
    )

    project_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == project_id


@pytest.mark.asyncio
async def test_update_project(client):
    token = await register_and_login(
        client,
        "update-project@example.com",
    )

    create_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "Old Name",
            "priority": "low",
        },
    )

    project_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(token),
        json={
            "name": "New Name",
            "priority": "high",
            "status": "in_progress",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Name"
    assert data["priority"] == "high"
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_project(client):
    token = await register_and_login(
        client,
        "delete-project@example.com",
    )

    create_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "Delete Project",
        },
    )

    project_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    get_response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_project_search(client):
    token = await register_and_login(
        client,
        "search-project@example.com",
    )

    await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "Python API",
        },
    )

    await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "React Dashboard",
        },
    )

    response = await client.get(
        "/api/v1/projects",
        headers=auth_headers(token),
        params={
            "search": "Python",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Python API"


@pytest.mark.asyncio
async def test_project_status_filter(client):
    token = await register_and_login(
        client,
        "status-project@example.com",
    )

    await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "Pending Project",
            "status": "pending",
        },
    )

    await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "Completed Project",
            "status": "completed",
        },
    )

    response = await client.get(
        "/api/v1/projects",
        headers=auth_headers(token),
        params={
            "status": "completed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Completed Project"


@pytest.mark.asyncio
async def test_project_priority_filter(client):
    token = await register_and_login(
        client,
        "priority-project@example.com",
    )

    await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "Low Project",
            "priority": "low",
        },
    )

    await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={
            "name": "High Project",
            "priority": "high",
        },
    )

    response = await client.get(
        "/api/v1/projects",
        headers=auth_headers(token),
        params={
            "priority": "high",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "High Project"


@pytest.mark.asyncio
async def test_project_ownership(client):
    user_a_token = await register_and_login(
        client,
        "user-a@example.com",
    )

    user_b_token = await register_and_login(
        client,
        "user-b@example.com",
    )

    create_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers(user_a_token),
        json={
            "name": "User A Private Project",
        },
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    # User B cannot read User A's project.
    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(user_b_token),
    )

    assert response.status_code == 404

    # User B cannot update User A's project.
    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(user_b_token),
        json={
            "name": "Hacked Project",
        },
    )

    assert response.status_code == 404

    # User B cannot delete User A's project.
    response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(user_b_token),
    )

    assert response.status_code == 404

    # User A's project must still exist.
    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers(user_a_token),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "User A Private Project"