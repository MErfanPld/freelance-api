from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user_public import PublicIdResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me/public-id",
    response_model=PublicIdResponse,
    summary="Get current user's public UUID",
)
async def get_my_public_id(
    current_user: User = Depends(get_current_user),
) -> PublicIdResponse:
    """
    Return the authenticated user's unique public ID (UUID).

    Used so collaborators can share their ID with a project owner for invitations.
    Does not accept a user id from the client — always returns the token subject.
    """
    return PublicIdResponse(id=current_user.id)
