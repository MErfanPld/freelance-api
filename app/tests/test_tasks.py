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


async def create_project(client, token: str, name="Test Project"):
    response = await client.post(
        "/api/v1/projects",
        headers=auth_headers(token),
        json={"name": name},
    )

    assert response.status_code == 201
    return response.json()["id"]


async def create_task(
    client,
    token: str,
    project_id: str,
    title="Test Task",
    **kwargs,
):
    payload = {
        "project_id": project_id,
        "title": title,
    }
    payload.update(kwargs)

    response = await client.post(
        "/api/v1/tasks",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201
    return response


@pytest.mark.asyncio
async def test_create_task(client):
    token = await register_and_login(
        client,
        "task-create@example.com",
    )

    project_id = await create_project(client, token)

    response = await create_task(
        client,
        token,
        project_id,
        title="Build API",
        description="Implement FastAPI endpoints",
        status="todo",
        priority="high",
        estimated_hours="8.5",
        actual_hours="2.0",
    )

    data = response.json()

    assert data["title"] == "Build API"
    assert data["description"] == "Implement FastAPI endpoints"
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["project_id"] == project_id


@pytest.mark.asyncio
async def test_list_tasks(client):
    token = await register_and_login(
        client,
        "task-list@example.com",
    )

    project_id = await create_project(client, token)

    await create_task(
        client,
        token,
        project_id,
        title="Task One",
    )

    await create_task(
        client,
        token,
        project_id,
        title="Task Two",
    )

    response = await client.get(
        "/api/v1/tasks",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_task(client):
    token = await register_and_login(
        client,
        "task-get@example.com",
    )

    project_id = await create_project(client, token)

    create_response = await create_task(
        client,
        token,
        project_id,
        title="Get Task",
    )

    task_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "Get Task"


@pytest.mark.asyncio
async def test_update_task(client):
    token = await register_and_login(
        client,
        "task-update@example.com",
    )

    project_id = await create_project(client, token)

    create_response = await create_task(
        client,
        token,
        project_id,
        title="Old Task",
        priority="low",
    )

    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(token),
        json={
            "title": "Updated Task",
            "status": "in_progress",
            "priority": "high",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated Task"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_delete_task(client):
    token = await register_and_login(
        client,
        "task-delete@example.com",
    )

    project_id = await create_project(client, token)

    create_response = await create_task(
        client,
        token,
        project_id,
        title="Delete Task",
    )

    task_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    response = await client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_task_search(client):
    token = await register_and_login(
        client,
        "task-search@example.com",
    )

    project_id = await create_project(client, token)

    await create_task(
        client,
        token,
        project_id,
        title="Build Authentication",
    )

    await create_task(
        client,
        token,
        project_id,
        title="Build Dashboard",
    )

    response = await client.get(
        "/api/v1/tasks",
        headers=auth_headers(token),
        params={"search": "Authentication"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "Build Authentication"


@pytest.mark.asyncio
async def test_task_status_filter(client):
    token = await register_and_login(
        client,
        "task-status@example.com",
    )

    project_id = await create_project(client, token)

    await create_task(
        client,
        token,
        project_id,
        title="Todo Task",
        status="todo",
    )

    await create_task(
        client,
        token,
        project_id,
        title="Done Task",
        status="done",
    )

    response = await client.get(
        "/api/v1/tasks",
        headers=auth_headers(token),
        params={"status": "done"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "Done Task"


@pytest.mark.asyncio
async def test_task_priority_filter(client):
    token = await register_and_login(
        client,
        "task-priority@example.com",
    )

    project_id = await create_project(client, token)

    await create_task(
        client,
        token,
        project_id,
        title="Low Task",
        priority="low",
    )

    await create_task(
        client,
        token,
        project_id,
        title="High Task",
        priority="high",
    )

    response = await client.get(
        "/api/v1/tasks",
        headers=auth_headers(token),
        params={"priority": "high"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "High Task"


@pytest.mark.asyncio
async def test_task_due_date_filter(client):
    token = await register_and_login(
        client,
        "task-due-date@example.com",
    )

    project_id = await create_project(client, token)

    await create_task(
        client,
        token,
        project_id,
        title="Early Task",
        due_date="2026-09-10",
    )

    await create_task(
        client,
        token,
        project_id,
        title="Late Task",
        due_date="2026-09-30",
    )

    response = await client.get(
        "/api/v1/tasks",
        headers=auth_headers(token),
        params={
            "due_date_from": "2026-09-01",
            "due_date_to": "2026-09-15",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "Early Task"


@pytest.mark.asyncio
async def test_task_pagination(client):
    token = await register_and_login(
        client,
        "task-pagination@example.com",
    )

    project_id = await create_project(client, token)

    for i in range(5):
        await create_task(
            client,
            token,
            project_id,
            title=f"Task {i}",
        )

    response = await client.get(
        "/api/v1/tasks",
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
async def test_task_project_ownership_on_create(client):
    user_a_token = await register_and_login(
        client,
        "task-project-a@example.com",
    )

    user_b_token = await register_and_login(
        client,
        "task-project-b@example.com",
    )

    project_a_id = await create_project(
        client,
        user_a_token,
        "User A Project",
    )

    # User B must not be able to create a task
    # inside User A's project.
    response = await client.post(
        "/api/v1/tasks",
        headers=auth_headers(user_b_token),
        json={
            "project_id": project_a_id,
            "title": "Unauthorized Task",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_task_ownership_isolation(client):
    user_a_token = await register_and_login(
        client,
        "task-owner-a@example.com",
    )

    user_b_token = await register_and_login(
        client,
        "task-owner-b@example.com",
    )

    project_a_id = await create_project(
        client,
        user_a_token,
        "User A Project",
    )

    task_response = await create_task(
        client,
        user_a_token,
        project_a_id,
        title="Private Task",
    )

    task_id = task_response.json()["id"]

    # User B cannot GET.
    response = await client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(user_b_token),
    )

    assert response.status_code == 404

    # User B cannot PATCH.
    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(user_b_token),
        json={
            "title": "Hacked Task",
        },
    )

    assert response.status_code == 404

    # User B cannot DELETE.
    response = await client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(user_b_token),
    )

    assert response.status_code == 404

    # User B cannot see User A's tasks in list.
    response = await client.get(
        "/api/v1/tasks",
        headers=auth_headers(user_b_token),
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 0

    # User A still owns the task.
    response = await client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(user_a_token),
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Private Task"
