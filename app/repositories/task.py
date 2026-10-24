from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.project import Project
from app.models.project_member import ProjectMember


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _access_filter(self, user_id: str):
        return or_(
            Project.user_id == user_id,
            Project.id.in_(
                select(ProjectMember.project_id).where(
                    ProjectMember.user_id == user_id,
                    ProjectMember.status == "active",
                )
            ),
        )

    async def get_by_id(self, task_id: str, user_id: str) -> Task | None:
        result = await self.db.execute(
            select(Task)
            .join(Project, Task.project_id == Project.id)
            .where(Task.id == task_id, self._access_filter(user_id))
        )
        return result.scalar_one_or_none()

    async def count(
        self, *, user_id: str, project_id: str | None = None,
        search: str | None = None, status: str | None = None,
        priority: str | None = None, due_date_from: date | None = None,
        due_date_to: date | None = None,
    ) -> int:
        query = (
            select(func.count(Task.id))
            .join(Project, Task.project_id == Project.id)
            .where(self._access_filter(user_id))
        )
        query = self._apply_filters(
            query, project_id=project_id, search=search, status=status,
            priority=priority, due_date_from=due_date_from, due_date_to=due_date_to,
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def list(
        self, *, user_id: str, offset: int, limit: int,
        project_id: str | None = None, search: str | None = None,
        status: str | None = None, priority: str | None = None,
        due_date_from: date | None = None, due_date_to: date | None = None,
    ) -> list[Task]:
        query = (
            select(Task)
            .join(Project, Task.project_id == Project.id)
            .where(self._access_filter(user_id))
        )
        query = self._apply_filters(
            query, project_id=project_id, search=search, status=status,
            priority=priority, due_date_from=due_date_from, due_date_to=due_date_to,
        )
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _apply_filters(
        self, query, *, project_id, search, status, priority, due_date_from, due_date_to,
    ):
        if project_id:
            query = query.where(Task.project_id == project_id)
        if search:
            pattern = f"%{search}%"
            query = query.where(or_(Task.title.ilike(pattern), Task.description.ilike(pattern)))
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if due_date_from:
            query = query.where(Task.due_date >= due_date_from)
        if due_date_to:
            query = query.where(Task.due_date <= due_date_to)
        return query

    async def create(
        self, *, project_id: str, title: str, description: str | None,
        status: str, priority: str, estimated_hours: float | None,
        actual_hours: float | None, due_date: date | None,
        created_by_id: str | None = None, assignee_id: str | None = None,
    ) -> Task:
        task = Task(
            project_id=project_id, title=title, description=description,
            status=status, priority=priority, estimated_hours=estimated_hours,
            actual_hours=actual_hours, due_date=due_date,
            created_by_id=created_by_id, assignee_id=assignee_id,
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.db.delete(task)
        await self.db.flush()
