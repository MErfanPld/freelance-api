from datetime import date
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tasks = TaskRepository(db)

    async def _validate_project(
        self,
        project_id: str,
        user_id: str,
    ) -> Project:
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )

        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        return project

    async def create(
        self,
        user_id: str,
        data: TaskCreate,
    ) -> Task:
        await self._validate_project(
            data.project_id,
            user_id,
        )

        task = await self.tasks.create(
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            estimated_hours=data.estimated_hours,
            actual_hours=data.actual_hours,
            due_date=data.due_date,
        )

        await self.db.commit()

        return task

    async def get(
        self,
        task_id: str,
        user_id: str,
    ) -> Task:
        task = await self.tasks.get_by_id(
            task_id,
            user_id,
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return task

    async def list(
        self,
        *,
        user_id: str,
        page: int,
        page_size: int,
        project_id: str | None,
        search: str | None,
        status_filter: str | None,
        priority: str | None,
        due_date_from: date | None,
        due_date_to: date | None,
    ):
        if (
            due_date_from
            and due_date_to
            and due_date_to < due_date_from
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "due_date_to cannot be before "
                    "due_date_from"
                ),
            )

        if project_id:
            await self._validate_project(
                project_id,
                user_id,
            )

        total = await self.tasks.count(
            user_id=user_id,
            project_id=project_id,
            search=search,
            status=status_filter,
            priority=priority,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
        )

        offset = (page - 1) * page_size

        items = await self.tasks.list(
            user_id=user_id,
            offset=offset,
            limit=page_size,
            project_id=project_id,
            search=search,
            status=status_filter,
            priority=priority,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
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
        task_id: str,
        user_id: str,
        data: TaskUpdate,
    ) -> Task:
        task = await self.get(
            task_id,
            user_id,
        )

        values = data.model_dump(
            exclude_unset=True
        )

        for field, value in values.items():
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def delete(
        self,
        task_id: str,
        user_id: str,
    ) -> None:
        task = await self.get(
            task_id,
            user_id,
        )

        await self.tasks.delete(task)

        await self.db.commit()
