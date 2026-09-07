from datetime import date
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
)


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.projects = ProjectRepository(db)
        self.users = UserRepository(db)

    async def create(
        self,
        user_id: str,
        data: ProjectCreate,
    ) -> Project:
        if data.client_id:
            client = await self._validate_client(
                data.client_id,
                user_id,
            )

            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Client not found",
                )

        project = await self.projects.create(
            user_id=user_id,
            client_id=data.client_id,
            name=data.name,
            description=data.description,
            status=data.status,
            priority=data.priority,
            start_date=data.start_date,
            deadline=data.deadline,
            budget=data.budget,
        )

        await self.db.commit()

        return project

    async def get(
        self,
        project_id: str,
        user_id: str,
    ) -> Project:
        project = await self.projects.get_by_id(
            project_id,
            user_id,
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        return project

    async def list(
        self,
        *,
        user_id: str,
        page: int,
        page_size: int,
        search: str | None,
        status_filter: str | None,
        priority: str | None,
        deadline_from: date | None,
        deadline_to: date | None,
    ):
        if deadline_from and deadline_to:
            if deadline_to < deadline_from:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "deadline_to cannot be before "
                        "deadline_from"
                    ),
                )

        total = await self.projects.count(
            user_id=user_id,
            search=search,
            status=status_filter,
            priority=priority,
            deadline_from=deadline_from,
            deadline_to=deadline_to,
        )

        offset = (page - 1) * page_size

        items = await self.projects.list(
            user_id=user_id,
            offset=offset,
            limit=page_size,
            search=search,
            status=status_filter,
            priority=priority,
            deadline_from=deadline_from,
            deadline_to=deadline_to,
        )

        pages = ceil(total / page_size) if total else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    async def update(
        self,
        project_id: str,
        user_id: str,
        data: ProjectUpdate,
    ) -> Project:
        project = await self.get(
            project_id,
            user_id,
        )

        if data.client_id:
            client = await self._validate_client(
                data.client_id,
                user_id,
            )

            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Client not found",
                )

        values = data.model_dump(
            exclude_unset=True
        )

        for field, value in values.items():
            setattr(project, field, value)

        if (
            project.start_date
            and project.deadline
            and project.deadline < project.start_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deadline cannot be before start date",
            )

        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def delete(
        self,
        project_id: str,
        user_id: str,
    ) -> None:
        project = await self.get(
            project_id,
            user_id,
        )

        await self.projects.delete(project)
        await self.db.commit()

    async def _validate_client(
        self,
        client_id: str,
        user_id: str,
    ):
        from app.models.client import Client
        from sqlalchemy import select

        result = await self.db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()
