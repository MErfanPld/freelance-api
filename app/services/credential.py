from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_value, encrypt_value
from app.models.project import Project
from app.repositories.credential import CredentialRepository
from app.schemas.credential import (
    CredentialCreate,
    CredentialUpdate,
)


class CredentialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.credentials = CredentialRepository(db)

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

    async def create(
        self,
        user_id: str,
        data: CredentialCreate,
    ):
        await self._validate_project(
            data.project_id,
            user_id,
        )

        encrypted_password = encrypt_value(
            data.password
        )

        credential = await self.credentials.create(
            project_id=data.project_id,
            title=data.title,
            username=data.username,
            encrypted_password=encrypted_password,
            website=data.website,
            notes=data.notes,
        )

        await self.db.commit()
        await self.db.refresh(credential)

        return credential

    async def get(
        self,
        credential_id: str,
        user_id: str,
    ):
        credential = await self.credentials.get_by_id(
            credential_id,
            user_id,
        )

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found",
            )

        return credential

    async def list(
        self,
        user_id: str,
        project_id: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        if project_id:
            await self._validate_project(
                project_id,
                user_id,
            )

        total = await self.credentials.count(
            user_id=user_id,
            project_id=project_id,
            search=search,
        )

        items = await self.credentials.list(
            user_id=user_id,
            project_id=project_id,
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
        credential_id: str,
        user_id: str,
        data: CredentialUpdate,
    ):
        credential = await self.get(
            credential_id,
            user_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "password" in update_data:
            password = update_data.pop("password")

            credential.encrypted_password = encrypt_value(
                password
            )

        for field, value in update_data.items():
            setattr(credential, field, value)

        await self.db.commit()
        await self.db.refresh(credential)

        return credential

    async def delete(
        self,
        credential_id: str,
        user_id: str,
    ) -> None:
        credential = await self.get(
            credential_id,
            user_id,
        )

        await self.credentials.delete(credential)

        await self.db.commit()

    async def reveal(
        self,
        credential_id: str,
        user_id: str,
    ) -> dict:
        credential = await self.get(
            credential_id,
            user_id,
        )

        try:
            password = decrypt_value(
                credential.encrypted_password
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to decrypt credential",
            ) from exc

        return {
            "id": credential.id,
            "project_id": credential.project_id,
            "title": credential.title,
            "username": credential.username,
            "website": credential.website,
            "notes": credential.notes,
            "password": password,
        }
