from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project_member import ProjectMember
from app.models.user import User


class ProjectMemberRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, member_id: str) -> ProjectMember | None:
        result = await self.db.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.id == member_id)
        )
        return result.scalar_one_or_none()

    async def get_membership(
        self,
        project_id: str,
        user_id: str,
    ) -> ProjectMember | None:
        result = await self.db.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_membership(
        self,
        project_id: str,
        user_id: str,
    ) -> ProjectMember | None:
        result = await self.db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def list_for_project(
        self,
        project_id: str,
        *,
        status: str | None = None,
    ) -> list[ProjectMember]:
        query = (
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.project_id == project_id)
        )
        if status:
            query = query.where(ProjectMember.status == status)
        query = query.order_by(ProjectMember.created_at.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_active(self, project_id: str) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.status == "active",
            )
        )
        return int(result.scalar_one() or 0)

    async def create(
        self,
        *,
        project_id: str,
        user_id: str,
        role: str,
        status: str,
        invited_by_id: str | None = None,
    ) -> ProjectMember:
        now = datetime.now(timezone.utc)
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            status=status,
            invited_by_id=invited_by_id,
            invited_at=now if status == "pending" else None,
            joined_at=now if status == "active" else None,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def list_user_project_ids(
        self,
        user_id: str,
        *,
        active_only: bool = True,
    ) -> list[str]:
        conditions = [ProjectMember.user_id == user_id]
        if active_only:
            conditions.append(ProjectMember.status == "active")
        result = await self.db.execute(
            select(ProjectMember.project_id).where(and_(*conditions))
        )
        return list(result.scalars().all())

    async def list_pending_for_user(
        self,
        user_id: str,
    ) -> list[ProjectMember]:
        """Pending invitations for the given user (awaiting their response)."""
        result = await self.db.execute(
            select(ProjectMember)
            .options(
                selectinload(ProjectMember.project),
                selectinload(ProjectMember.invited_by),
            )
            .where(
                ProjectMember.user_id == user_id,
                ProjectMember.status == "pending",
            )
            .order_by(ProjectMember.invited_at.desc())
        )
        return list(result.scalars().all())
