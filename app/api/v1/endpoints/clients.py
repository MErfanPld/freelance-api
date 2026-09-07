from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.client import (
    ClientCreate,
    ClientListResponse,
    ClientResponse,
    ClientUpdate,
)
from app.services.client import ClientService


router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
)


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ClientService(db).create(
        current_user.id,
        data,
    )


@router.get(
    "",
    response_model=ClientListResponse,
)
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    search: str | None = Query(
        None,
        max_length=200,
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ClientService(db).list(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
)
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ClientService(db).get(
        client_id,
        current_user.id,
    )


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
)
async def update_client(
    client_id: str,
    data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ClientService(db).update(
        client_id,
        current_user.id,
        data,
    )


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ClientService(db).delete(
        client_id,
        current_user.id,
    )
