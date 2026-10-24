from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.project_member import ProjectMember
from app.repositories.project_member import ProjectMemberRepository
from app.repositories.user import UserRepository
from app.schemas.project_member import ProjectInviteCreate
from app.utils.permissions import require_active_member, require_owner


class ProjectMemberService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.members = ProjectMemberRepository(db)
        self.users = UserRepository(db)

    async def invite(self, project_id: str, inviter_id: str, data: ProjectInviteCreate) -> ProjectMember:
        if data.user_id == inviter_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot invite yourself")
        await require_owner(self.db, project_id, inviter_id)
        target = await self.users.get_by_id(data.user_id)
        if not target or not target.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        existing = await self.members.get_membership(project_id, data.user_id)
        if existing:
            if existing.status == "active":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this project")
            if existing.status == "pending":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An invitation is already pending for this user")
            existing.role = data.role
            existing.status = "pending"
            existing.invited_by_id = inviter_id
            existing.invited_at = datetime.now(timezone.utc)
            existing.joined_at = None
            member = existing
        else:
            member = await self.members.create(
                project_id=project_id, user_id=data.user_id, role=data.role,
                status="pending", invited_by_id=inviter_id,
            )
        inviter = await self.users.get_by_id(inviter_id)
        from app.models.project import Project
        from sqlalchemy import select
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        proj = result.scalar_one()
        notif = Notification(
            user_id=data.user_id, type="project_invitation", title="Project invitation",
            message=f'{inviter.first_name} {inviter.last_name} invited you to project "{proj.name}"',
            data={"project_id": project_id, "member_id": member.id, "role": data.role},
            project_id=project_id,
        )
        self.db.add(notif)
        await self.db.commit()
        member = await self.members.get_by_id(member.id)
        return member

    async def accept(self, project_id: str, user_id: str) -> ProjectMember:
        member = await self.members.get_membership(project_id, user_id)
        if not member or member.status != "pending":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending invitation not found")
        if member.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        member.status = "active"
        member.joined_at = datetime.now(timezone.utc)
        if member.invited_by_id:
            from app.models.project import Project
            from sqlalchemy import select
            result = await self.db.execute(select(Project).where(Project.id == project_id))
            proj = result.scalar_one_or_none()
            user = await self.users.get_by_id(user_id)
            if proj and user:
                notif = Notification(
                    user_id=member.invited_by_id, type="invitation_accepted", title="Invitation accepted",
                    message=f'{user.first_name} {user.last_name} accepted the invitation to "{proj.name}"',
                    data={"project_id": project_id, "member_id": member.id}, project_id=project_id,
                )
                self.db.add(notif)
        await self.db.commit()
        member = await self.members.get_by_id(member.id)
        return member

    async def reject(self, project_id: str, user_id: str) -> ProjectMember:
        member = await self.members.get_membership(project_id, user_id)
        if not member or member.status != "pending":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending invitation not found")
        if member.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        member.status = "rejected"
        if member.invited_by_id:
            from app.models.project import Project
            from sqlalchemy import select
            result = await self.db.execute(select(Project).where(Project.id == project_id))
            proj = result.scalar_one_or_none()
            user = await self.users.get_by_id(user_id)
            if proj and user:
                notif = Notification(
                    user_id=member.invited_by_id, type="invitation_rejected", title="Invitation rejected",
                    message=f'{user.first_name} {user.last_name} rejected the invitation to "{proj.name}"',
                    data={"project_id": project_id, "member_id": member.id}, project_id=project_id,
                )
                self.db.add(notif)
        await self.db.commit()
        member = await self.members.get_by_id(member.id)
        return member

    async def cancel_invitation(self, project_id: str, member_id: str, actor_id: str) -> None:
        await require_owner(self.db, project_id, actor_id)
        member = await self.members.get_by_id(member_id)
        if not member or member.project_id != project_id or member.status != "pending":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending invitation not found")
        await self.db.delete(member)
        await self.db.commit()

    async def leave(self, project_id: str, user_id: str) -> None:
        member = await self.members.get_membership(project_id, user_id)
        if not member or member.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
        if member.role == "owner":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project owner cannot leave; transfer ownership or delete the project")
        member.status = "left"
        await self.db.commit()

    async def remove_member(self, project_id: str, member_id: str, actor_id: str) -> None:
        await require_owner(self.db, project_id, actor_id)
        member = await self.members.get_by_id(member_id)
        if not member or member.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        if member.role == "owner" or member.user_id == actor_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the project owner")
        if member.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member is not active")
        member.status = "removed"
        await self.db.commit()

    async def list_members(self, project_id: str, user_id: str, status_filter: str | None = None) -> list[ProjectMember]:
        await require_active_member(self.db, project_id, user_id)
        return await self.members.list_for_project(project_id, status=status_filter)

    async def lookup_user(self, user_id: str, current_user_id: str):
        if user_id == current_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot look up yourself as a collaborator")
        user = await self.users.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
