from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.project import Project
from app.repositories.note import NoteRepository
from app.schemas.note import NoteCreate, NoteUpdate


class NoteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notes = NoteRepository(db)

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

    async def _validate_client(
        self,
        client_id: str,
        user_id: str,
    ) -> Client:
        result = await self.db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.user_id == user_id,
            )
        )

        client = result.scalar_one_or_none()

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        return client

    async def create(
        self,
        user_id: str,
        data: NoteCreate,
    ):
        await self._validate_project(
            data.project_id,
            user_id,
        )

        if data.client_id:
            await self._validate_client(
                data.client_id,
                user_id,
            )

        note = await self.notes.create(
            project_id=data.project_id,
            client_id=data.client_id,
            title=data.title,
            content=data.content,
        )

        await self.db.commit()
        await self.db.refresh(note)

        return note

    async def get(
        self,
        note_id: str,
        user_id: str,
    ):
        note = await self.notes.get_by_id(
            note_id,
            user_id,
        )

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

        return note

    async def list(
        self,
        user_id: str,
        project_id: str | None = None,
        client_id: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        if project_id:
            await self._validate_project(
                project_id,
                user_id,
            )

        if client_id:
            await self._validate_client(
                client_id,
                user_id,
            )

        total = await self.notes.count(
            user_id=user_id,
            project_id=project_id,
            client_id=client_id,
            search=search,
        )

        items = await self.notes.list(
            user_id=user_id,
            project_id=project_id,
            client_id=client_id,
            search=search,
            offset=(page - 1) * page_size,
            limit=page_size,
        )

        pages = (
            (total + page_size - 1) // page_size
            if total
            else 0
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    async def update(
        self,
        note_id: str,
        user_id: str,
        data: NoteUpdate,
    ):
        note = await self.get(
            note_id,
            user_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "client_id" in update_data:
            client_id = update_data["client_id"]

            if client_id:
                await self._validate_client(
                    client_id,
                    user_id,
                )

        for field, value in update_data.items():
            setattr(note, field, value)

        await self.db.commit()
        await self.db.refresh(note)

        return note

    async def delete(
        self,
        note_id: str,
        user_id: str,
    ) -> None:
        note = await self.get(
            note_id,
            user_id,
        )

        await self.notes.delete(note)

        await self.db.commit()
