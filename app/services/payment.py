from datetime import date
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.project import Project
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.utils.permissions import require_active_member


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payments = PaymentRepository(db)

    async def _validate_project(self, project_id: str, user_id: str) -> Project:
        await require_active_member(self.db, project_id, user_id)
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    async def create(self, user_id: str, data: PaymentCreate) -> Payment:
        await self._validate_project(data.project_id, user_id)
        payment = await self.payments.create(
            project_id=data.project_id,
            amount=data.amount,
            payment_type=data.type,
            payment_status=data.status,
            payment_date=data.payment_date,
            description=data.description,
        )
        await self.db.commit()
        return payment

    async def get(self, payment_id: str, user_id: str) -> Payment:
        payment = await self.payments.get_by_id(payment_id, user_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        return payment

    async def list(
        self, *, user_id: str, page: int, page_size: int, project_id: str | None,
        payment_type: str | None, payment_status: str | None,
        date_from: date | None, date_to: date | None,
    ):
        if date_from and date_to and date_to < date_from:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_to cannot be before date_from")
        if project_id:
            await self._validate_project(project_id, user_id)
        total = await self.payments.count(
            user_id=user_id, project_id=project_id, payment_type=payment_type,
            payment_status=payment_status, date_from=date_from, date_to=date_to,
        )
        offset = (page - 1) * page_size
        items = await self.payments.list(
            user_id=user_id, offset=offset, limit=page_size, project_id=project_id,
            payment_type=payment_type, payment_status=payment_status,
            date_from=date_from, date_to=date_to,
        )
        pages = ceil(total / page_size) if total else 0
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}

    async def update(self, payment_id: str, user_id: str, data: PaymentUpdate) -> Payment:
        payment = await self.get(payment_id, user_id)
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(payment, field, value)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def delete(self, payment_id: str, user_id: str) -> None:
        payment = await self.get(payment_id, user_id)
        await self.payments.delete(payment)
        await self.db.commit()

    async def summary(self, *, user_id: str, project_id: str | None, date_from: date | None, date_to: date | None):
        if date_from and date_to and date_to < date_from:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_to cannot be before date_from")
        if project_id:
            await self._validate_project(project_id, user_id)
        return await self.payments.summary(
            user_id=user_id, project_id=project_id, date_from=date_from, date_to=date_to,
        )

    async def monthly_summary(self, *, user_id: str, year: int, month: int):
        if month < 1 or month > 12:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Month must be between 1 and 12")
        return await self.payments.monthly_summary(user_id=user_id, year=year, month=month)
