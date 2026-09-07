from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services.task import TaskService


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).create(
        current_user.id,
        data,
    )


@router.get(
    "",
    response_model=TaskListResponse,
)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    project_id: str | None = None,
    search: str | None = Query(
        None,
        max_length=200,
    ),
    status_filter: str | None = Query(
        None,
        alias="status",
    ),
    priority: str | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).list(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        project_id=project_id,
        search=search,
        status_filter=status_filter,
        priority=priority,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).get(
        task_id,
        current_user.id,
    )


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).update(
        task_id,
        current_user.id,
        data,
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await TaskService(db).delete(
        task_id,
        current_user.id,
    )
