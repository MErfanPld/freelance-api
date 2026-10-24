from datetime import date
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.project import ProjectRepository
from app.repositories.project_member import ProjectMemberRepository
from app.repositories.user import UserRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.utils.permissions import require_active_member, require_owner


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.projects = ProjectRepository(db)
        self.members = ProjectMemberRepository(db)
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

        # Owner membership
        await self.members.create(
            project_id=project.id,
            user_id=user_id,
            role="owner",
            status="active",
        )

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get(
        self,
        project_id: str,
        user_id: str,
    ) -> Project:
        await require_active_member(self.db, project_id, user_id)
        project = await self.projects.get_by_id(project_id)
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
                    detail="deadline_to cannot be before deadline_from",
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
        await require_owner(self.db, project_id, user_id)
        project = await self.projects.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
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

        values = data.model_dump(exclude_unset=True)
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
        await require_owner(self.db, project_id, user_id)
        project = await self.projects.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        await self.projects.delete(project)
        await self.db.commit()

    async def archive(
        self,
        project_id: str,
        user_id: str,
    ) -> Project:
        await require_owner(self.db, project_id, user_id)
        project = await self.projects.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        project.status = "cancelled"
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def _validate_client(
        self,
        client_id: str,
        user_id: str,
    ):
        from app.models.client import Client

        result = await self.db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
