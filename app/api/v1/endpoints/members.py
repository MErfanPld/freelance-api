from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.project_member import (
    PendingInvitationListResponse,
    PendingInvitationResponse,
    ProjectInviteCreate,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    PublicUserResponse,
)
from app.services.project_member import ProjectMemberService


router = APIRouter(tags=["Project Members"])


@router.get(
    "/me/invitations",
    response_model=PendingInvitationListResponse,
    summary="List my pending project invitations",
)
async def list_my_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Invitations with status=pending for the authenticated user.

    Use POST /projects/{project_id}/invitations/accept or .../reject to respond.
    Until accepted, the user is not an active member and cannot access project tasks.
    """
    members = await ProjectMemberService(db).list_my_pending_invitations(
        current_user.id,
    )
    items = []
    for m in members:
        project_name = None
        if getattr(m, "project", None) is not None:
            project_name = m.project.name
        inv_fn = inv_ln = None
        if getattr(m, "invited_by", None) is not None:
            inv_fn = m.invited_by.first_name
            inv_ln = m.invited_by.last_name
        items.append(
            PendingInvitationResponse(
                id=m.id,
                project_id=m.project_id,
                project_name=project_name,
                user_id=m.user_id,
                role=m.role,
                status=m.status,
                invited_by_id=m.invited_by_id,
                invited_by_first_name=inv_fn,
                invited_by_last_name=inv_ln,
                invited_at=m.invited_at,
            )
        )
    return PendingInvitationListResponse(items=items, total=len(items))


@router.get(
    "/users/{user_id}/public",
    response_model=PublicUserResponse,
)
async def lookup_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await ProjectMemberService(db).lookup_user(
        user_id,
        current_user.id,
    )
    return PublicUserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
    )


@router.post(
    "/projects/{project_id}/invitations",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    project_id: str,
    data: ProjectInviteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await ProjectMemberService(db).invite(
        project_id,
        current_user.id,
        data,
    )
    return _to_response(member)


@router.post(
    "/projects/{project_id}/invitations/accept",
    response_model=ProjectMemberResponse,
)
async def accept_invitation(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await ProjectMemberService(db).accept(
        project_id,
        current_user.id,
    )
    return _to_response(member)


@router.post(
    "/projects/{project_id}/invitations/reject",
    response_model=ProjectMemberResponse,
)
async def reject_invitation(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await ProjectMemberService(db).reject(
        project_id,
        current_user.id,
    )
    return _to_response(member)


@router.delete(
    "/projects/{project_id}/invitations/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_invitation(
    project_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ProjectMemberService(db).cancel_invitation(
        project_id,
        member_id,
        current_user.id,
    )


@router.get(
    "/projects/{project_id}/members",
    response_model=ProjectMemberListResponse,
)
async def list_members(
    project_id: str,
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    members = await ProjectMemberService(db).list_members(
        project_id,
        current_user.id,
        status_filter,
    )
    items = [_to_response(m) for m in members]
    return ProjectMemberListResponse(items=items, total=len(items))


@router.post(
    "/projects/{project_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ProjectMemberService(db).leave(project_id, current_user.id)


@router.delete(
    "/projects/{project_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    project_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ProjectMemberService(db).remove_member(
        project_id,
        member_id,
        current_user.id,
    )


def _to_response(member) -> ProjectMemberResponse:
    first_name = None
    last_name = None
    if hasattr(member, "user") and member.user is not None:
        first_name = member.user.first_name
        last_name = member.user.last_name
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        status=member.status,
        invited_by_id=member.invited_by_id,
        invited_at=member.invited_at,
        joined_at=member.joined_at,
        first_name=first_name,
        last_name=last_name,
    )
