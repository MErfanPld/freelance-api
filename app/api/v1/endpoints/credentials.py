from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.credential import (
    CredentialCreate,
    CredentialListResponse,
    CredentialResponse,
    CredentialRevealResponse,
    CredentialUpdate,
)
from app.services.credential import CredentialService


router = APIRouter(
    prefix="/credentials",
    tags=["Credentials"],
)


@router.post(
    "",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_credential(
    data: CredentialCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CredentialService(db).create(
        current_user.id,
        data,
    )


@router.get(
    "",
    response_model=CredentialListResponse,
)
async def list_credentials(
    project_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CredentialService(db).list(
        user_id=current_user.id,
        project_id=project_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{credential_id}/reveal",
    response_model=CredentialRevealResponse,
)
async def reveal_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CredentialService(db).reveal(
        credential_id,
        current_user.id,
    )


@router.get(
    "/{credential_id}",
    response_model=CredentialResponse,
)
async def get_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CredentialService(db).get(
        credential_id,
        current_user.id,
    )


@router.patch(
    "/{credential_id}",
    response_model=CredentialResponse,
)
async def update_credential(
    credential_id: str,
    data: CredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CredentialService(db).update(
        credential_id,
        current_user.id,
        data,
    )


@router.delete(
    "/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CredentialService(db).delete(
        credential_id,
        current_user.id,
    )
