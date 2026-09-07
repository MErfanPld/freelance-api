from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.note import (
    NoteCreate,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
)
from app.services.note import NoteService


router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NoteService(db).create(
        current_user.id,
        data,
    )


@router.get(
    "",
    response_model=NoteListResponse,
)
async def list_notes(
    project_id: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
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
    return await NoteService(db).list(
        user_id=current_user.id,
        project_id=project_id,
        client_id=client_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NoteService(db).get(
        note_id,
        current_user.id,
    )


@router.patch(
    "/{note_id}",
    response_model=NoteResponse,
)
async def update_note(
    note_id: str,
    data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NoteService(db).update(
        note_id,
        current_user.id,
        data,
    )


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await NoteService(db).delete(
        note_id,
        current_user.id,
    )
