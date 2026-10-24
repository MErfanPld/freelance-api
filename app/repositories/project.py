from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        project_id: str,
        user_id: str | None = None,
    ) -> Project | None:
        """If user_id is provided, only return if user owns or is active member."""
        if user_id is None:
            result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            return result.scalar_one_or_none()

        # Owner or active member
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                or_(
                    Project.user_id == user_id,
                    Project.id.in_(
                        select(ProjectMember.project_id).where(
                            ProjectMember.user_id == user_id,
                            ProjectMember.status == "active",
                        )
                    ),
                ),
            )
        )
        return result.scalar_one_or_none()

    def _accessible_condition(self, user_id: str):
        return or_(
            Project.user_id == user_id,
            Project.id.in_(
                select(ProjectMember.project_id).where(
                    ProjectMember.user_id == user_id,
                    ProjectMember.status == "active",
                )
            ),
        )

    async def count(
        self,
        *,
        user_id: str,
        search: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        deadline_from: date | None = None,
        deadline_to: date | None = None,
    ) -> int:
        query = select(func.count(Project.id)).where(
            self._accessible_condition(user_id)
        )
        query = self._apply_filters(
            query,
            search=search,
            status=status,
            priority=priority,
            deadline_from=deadline_from,
            deadline_to=deadline_to,
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def list(
        self,
        *,
        user_id: str,
        offset: int,
        limit: int,
        search: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        deadline_from: date | None = None,
        deadline_to: date | None = None,
    ) -> list[Project]:
        query = select(Project).where(
            self._accessible_condition(user_id)
        )
        query = self._apply_filters(
            query,
            search=search,
            status=status,
            priority=priority,
            deadline_from=deadline_from,
            deadline_to=deadline_to,
        )
        query = query.order_by(Project.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _apply_filters(
        self,
        query,
        *,
        search: str | None,
        status: str | None,
        priority: str | None,
        deadline_from: date | None,
        deadline_to: date | None,
    ):
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_pattern),
                    Project.description.ilike(search_pattern),
                )
            )
        if status:
            query = query.where(Project.status == status)
        if priority:
            query = query.where(Project.priority == priority)
        if deadline_from:
            query = query.where(Project.deadline >= deadline_from)
        if deadline_to:
            query = query.where(Project.deadline <= deadline_to)
        return query

    async def create(
        self,
        *,
        user_id: str,
        client_id: str | None,
        name: str,
        description: str | None,
        status: str,
        priority: str,
        start_date: date | None,
        deadline: date | None,
        budget,
    ) -> Project:
        project = Project(
            user_id=user_id,
            client_id=client_id,
            name=name,
            description=description,
            status=status,
            priority=priority,
            start_date=start_date,
            deadline=deadline,
            budget=budget,
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.flush()
