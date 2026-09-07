from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client


class ClientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        client_id: str,
        user_id: str,
    ) -> Client | None:
        result = await self.db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def count(
        self,
        *,
        user_id: str,
        search: str | None = None,
    ) -> int:
        query = select(
            func.count(Client.id)
        ).where(
            Client.user_id == user_id
        )

        query = self._apply_filters(
            query,
            search=search,
        )

        result = await self.db.execute(query)

        return result.scalar_one()

    async def list(
        self,
        *,
        user_id: str,
        offset: int,
        limit: int,
        search: str | None = None,
    ) -> list[Client]:
        query = select(Client).where(
            Client.user_id == user_id
        )

        query = self._apply_filters(
            query,
            search=search,
        )

        query = (
            query
            .order_by(Client.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    def _apply_filters(
        self,
        query,
        *,
        search: str | None,
    ):
        if search:
            query = query.where(
                Client.name.ilike(
                    f"%{search}%"
                )
            )

        return query

    async def create(
        self,
        *,
        user_id: str,
        name: str,
        company: str | None,
        email: str | None,
        phone: str | None,
        address: str | None,
        notes: str | None,
    ) -> Client:
        client = Client(
            user_id=user_id,
            name=name,
            company=company,
            email=email,
            phone=phone,
            address=address,
            notes=notes,
        )

        self.db.add(client)

        await self.db.flush()
        await self.db.refresh(client)

        return client

    async def delete(
        self,
        client: Client,
    ) -> None:
        await self.db.delete(client)
        await self.db.flush()
