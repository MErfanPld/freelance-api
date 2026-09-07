from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credential import Credential
from app.models.project import Project


class CredentialRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        credential_id: str,
        user_id: str,
    ) -> Credential | None:
        result = await self.db.execute(
            select(Credential)
            .join(Project, Credential.project_id == Project.id)
            .where(
                Credential.id == credential_id,
                Project.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def count(
        self,
        user_id: str,
        project_id: str | None = None,
        search: str | None = None,
    ) -> int:
        query = (
            select(func.count(Credential.id))
            .join(
                Project,
                Credential.project_id == Project.id,
            )
            .where(Project.user_id == user_id)
        )

        if project_id:
            query = query.where(
                Credential.project_id == project_id
            )

        if search:
            query = query.where(
                Credential.title.ilike(f"%{search}%")
            )

        result = await self.db.execute(query)

        return result.scalar_one()

    async def list(
        self,
        user_id: str,
        project_id: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Credential]:
        query = (
            select(Credential)
            .join(
                Project,
                Credential.project_id == Project.id,
            )
            .where(Project.user_id == user_id)
            .order_by(Credential.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        if project_id:
            query = query.where(
                Credential.project_id == project_id
            )

        if search:
            query = query.where(
                Credential.title.ilike(f"%{search}%")
            )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def create(
        self,
        *,
        project_id: str,
        title: str,
        username: str | None,
        encrypted_password: str,
        website: str | None,
        notes: str | None,
    ) -> Credential:
        credential = Credential(
            project_id=project_id,
            title=title,
            username=username,
            encrypted_password=encrypted_password,
            website=website,
            notes=notes,
        )

        self.db.add(credential)

        await self.db.flush()
        await self.db.refresh(credential)

        return credential

    async def delete(
        self,
        credential: Credential,
    ) -> None:
        await self.db.delete(credential)
        await self.db.flush()
