from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.repositories.client import ClientRepository
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
)


class ClientService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.clients = ClientRepository(db)

    async def create(
        self,
        user_id: str,
        data: ClientCreate,
    ) -> Client:
        client = await self.clients.create(
            user_id=user_id,
            name=data.name,
            company=data.company,
            email=data.email,
            phone=data.phone,
            address=data.address,
            notes=data.notes,
        )

        await self.db.commit()

        return client

    async def get(
        self,
        client_id: str,
        user_id: str,
    ) -> Client:
        client = await self.clients.get_by_id(
            client_id,
            user_id,
        )

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        return client

    async def list(
        self,
        *,
        user_id: str,
        page: int,
        page_size: int,
        search: str | None,
    ):
        total = await self.clients.count(
            user_id=user_id,
            search=search,
        )

        offset = (page - 1) * page_size

        items = await self.clients.list(
            user_id=user_id,
            offset=offset,
            limit=page_size,
            search=search,
        )

        pages = ceil(total / page_size) if total else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    async def update(
        self,
        client_id: str,
        user_id: str,
        data: ClientUpdate,
    ) -> Client:
        client = await self.get(
            client_id,
            user_id,
        )

        values = data.model_dump(
            exclude_unset=True
        )

        for field, value in values.items():
            setattr(client, field, value)

        await self.db.commit()
        await self.db.refresh(client)

        return client

    async def delete(
        self,
        client_id: str,
        user_id: str,
    ) -> None:
        client = await self.get(
            client_id,
            user_id,
        )

        await self.clients.delete(client)

        await self.db.commit()
