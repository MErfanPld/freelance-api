from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project import ProjectService


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ProjectService(db).create(
        current_user.id,
        data,
    )


@router.get(
    "",
    response_model=ProjectListResponse,
)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    search: str | None = Query(
        None,
        max_length=200,
    ),
    status_filter: str | None = Query(
        None,
        alias="status",
    ),
    priority: str | None = None,
    deadline_from: date | None = None,
    deadline_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ProjectService(db).list(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status_filter,
        priority=priority,
        deadline_from=deadline_from,
        deadline_to=deadline_to,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ProjectService(db).get(
        project_id,
        current_user.id,
    )


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ProjectService(db).update(
        project_id,
        current_user.id,
        data,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ProjectService(db).delete(
        project_id,
        current_user.id,
    )
