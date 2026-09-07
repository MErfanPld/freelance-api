from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.models.project import Project


class NoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        note_id: str,
        user_id: str,
    ) -> Note | None:
        result = await self.db.execute(
            select(Note)
            .join(Project, Note.project_id == Project.id)
            .where(
                Note.id == note_id,
                Project.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def count(
        self,
        user_id: str,
        project_id: str | None = None,
        client_id: str | None = None,
        search: str | None = None,
    ) -> int:
        query = (
            select(func.count(Note.id))
            .join(
                Project,
                Note.project_id == Project.id,
            )
            .where(Project.user_id == user_id)
        )

        if project_id:
            query = query.where(
                Note.project_id == project_id
            )

        if client_id:
            query = query.where(
                Note.client_id == client_id
            )

        if search:
            search_pattern = f"%{search}%"

            query = query.where(
                Note.title.ilike(search_pattern)
                | Note.content.ilike(search_pattern)
            )

        result = await self.db.execute(query)

        return result.scalar_one()

    async def list(
        self,
        user_id: str,
        project_id: str | None = None,
        client_id: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Note]:
        query = (
            select(Note)
            .join(
                Project,
                Note.project_id == Project.id,
            )
            .where(Project.user_id == user_id)
            .order_by(Note.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        if project_id:
            query = query.where(
                Note.project_id == project_id
            )

        if client_id:
            query = query.where(
                Note.client_id == client_id
            )

        if search:
            search_pattern = f"%{search}%"

            query = query.where(
                Note.title.ilike(search_pattern)
                | Note.content.ilike(search_pattern)
            )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def create(
        self,
        *,
        project_id: str,
        client_id: str | None,
        title: str,
        content: str,
    ) -> Note:
        note = Note(
            project_id=project_id,
            client_id=client_id,
            title=title,
            content=content,
        )

        self.db.add(note)

        await self.db.flush()
        await self.db.refresh(note)

        return note

    async def delete(
        self,
        note: Note,
    ) -> None:
        await self.db.delete(note)
        await self.db.flush()
