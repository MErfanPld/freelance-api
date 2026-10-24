"""Server-side access control helpers for collaborative projects."""

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember


async def get_project_or_404(
    db: AsyncSession,
    project_id: str,
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


async def get_membership(
    db: AsyncSession,
    project_id: str,
    user_id: str,
) -> ProjectMember | None:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def require_active_member(
    db: AsyncSession,
    project_id: str,
    user_id: str,
) -> ProjectMember:
    """Raise 404 if project missing or user is not an active member.

    Uses 404 (not 403) to avoid leaking project existence.
    """
    member = await get_membership(db, project_id, user_id)
    if not member or member.status != "active":
        # Also allow legacy owner via Project.user_id if no membership row yet
        result = await db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )
        project = result.scalar_one_or_none()
        if project:
            # Ensure membership exists for legacy projects
            from app.repositories.project_member import ProjectMemberRepository
            repo = ProjectMemberRepository(db)
            existing = await repo.get_membership(project_id, user_id)
            if not existing:
                member = await repo.create(
                    project_id=project_id,
                    user_id=user_id,
                    role="owner",
                    status="active",
                )
                await db.flush()
                return member
            if existing.status == "active":
                return existing
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return member


async def require_owner(
    db: AsyncSession,
    project_id: str,
    user_id: str,
) -> ProjectMember:
    member = await require_active_member(db, project_id, user_id)
    if member.role != "owner":
        # Fallback: Project.user_id is always the canonical owner
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project and project.user_id == user_id:
            return member
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can perform this action",
        )
    return member


async def user_can_access_project(
    db: AsyncSession,
    project_id: str,
    user_id: str,
) -> bool:
    try:
        await require_active_member(db, project_id, user_id)
        return True
    except HTTPException:
        return False


async def get_accessible_project_ids(
    db: AsyncSession,
    user_id: str,
) -> list[str]:
    """Project IDs the user owns or is an active member of."""
    # Owned
    owned = await db.execute(
        select(Project.id).where(Project.user_id == user_id)
    )
    owned_ids = set(owned.scalars().all())

    # Active memberships
    members = await db.execute(
        select(ProjectMember.project_id).where(
            ProjectMember.user_id == user_id,
            ProjectMember.status == "active",
        )
    )
    member_ids = set(members.scalars().all())

    return list(owned_ids | member_ids)
