from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.project import Project


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        payment_id: str,
        user_id: str,
    ) -> Payment | None:
        result = await self.db.execute(
            select(Payment)
            .join(
                Project,
                Payment.project_id == Project.id,
            )
            .where(
                Payment.id == payment_id,
                Project.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def count(
        self,
        *,
        user_id: str,
        project_id: str | None = None,
        payment_type: str | None = None,
        payment_status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int:
        query = (
            select(func.count(Payment.id))
            .join(
                Project,
                Payment.project_id == Project.id,
            )
            .where(
                Project.user_id == user_id
            )
        )

        query = self._apply_filters(
            query,
            project_id=project_id,
            payment_type=payment_type,
            payment_status=payment_status,
            date_from=date_from,
            date_to=date_to,
        )

        result = await self.db.execute(query)

        return result.scalar_one()

    async def list(
        self,
        *,
        user_id: str,
        offset: int,
        limit: int,
        project_id: str | None = None,
        payment_type: str | None = None,
        payment_status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Payment]:
        query = (
            select(Payment)
            .join(
                Project,
                Payment.project_id == Project.id,
            )
            .where(
                Project.user_id == user_id
            )
        )

        query = self._apply_filters(
            query,
            project_id=project_id,
            payment_type=payment_type,
            payment_status=payment_status,
            date_from=date_from,
            date_to=date_to,
        )

        query = (
            query
            .order_by(
                Payment.payment_date.desc(),
                Payment.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def summary(
        self,
        *,
        user_id: str,
        project_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        query = (
            select(
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.type == "income"
                    ),
                    0,
                ).label("total_income"),
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.type == "expense"
                    ),
                    0,
                ).label("total_expense"),
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.status == "paid"
                    ),
                    0,
                ).label("total_paid"),
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.status == "unpaid"
                    ),
                    0,
                ).label("total_unpaid"),
            )
            .join(
                Project,
                Payment.project_id == Project.id,
            )
            .where(
                Project.user_id == user_id
            )
        )

        query = self._apply_summary_filters(
            query,
            project_id=project_id,
            date_from=date_from,
            date_to=date_to,
        )

        result = await self.db.execute(query)

        row = result.one()

        total_income = row.total_income or 0
        total_expense = row.total_expense or 0

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "total_paid": row.total_paid or 0,
            "total_unpaid": row.total_unpaid or 0,
            "profit": total_income - total_expense,
        }

    async def monthly_summary(
        self,
        *,
        user_id: str,
        year: int,
        month: int,
    ) -> dict:
        query = (
            select(
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.type == "income"
                    ),
                    0,
                ).label("total_income"),
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.type == "expense"
                    ),
                    0,
                ).label("total_expense"),
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.status == "paid"
                    ),
                    0,
                ).label("total_paid"),
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.status == "unpaid"
                    ),
                    0,
                ).label("total_unpaid"),
            )
            .join(
                Project,
                Payment.project_id == Project.id,
            )
            .where(
                Project.user_id == user_id,
                func.strftime(
                    "%Y",
                    Payment.payment_date,
                ) == f"{year:04d}",
                func.strftime(
                    "%m",
                    Payment.payment_date,
                ) == f"{month:02d}",
            )
        )

        result = await self.db.execute(query)

        row = result.one()

        total_income = row.total_income or 0
        total_expense = row.total_expense or 0

        return {
            "year": year,
            "month": month,
            "total_income": total_income,
            "total_expense": total_expense,
            "total_paid": row.total_paid or 0,
            "total_unpaid": row.total_unpaid or 0,
            "profit": total_income - total_expense,
        }

    def _apply_filters(
        self,
        query,
        *,
        project_id: str | None,
        payment_type: str | None,
        payment_status: str | None,
        date_from: date | None,
        date_to: date | None,
    ):
        if project_id:
            query = query.where(
                Payment.project_id == project_id
            )

        if payment_type:
            query = query.where(
                Payment.type == payment_type
            )

        if payment_status:
            query = query.where(
                Payment.status == payment_status
            )

        if date_from:
            query = query.where(
                Payment.payment_date >= date_from
            )

        if date_to:
            query = query.where(
                Payment.payment_date <= date_to
            )

        return query

    def _apply_summary_filters(
        self,
        query,
        *,
        project_id: str | None,
        date_from: date | None,
        date_to: date | None,
    ):
        if project_id:
            query = query.where(
                Payment.project_id == project_id
            )

        if date_from:
            query = query.where(
                Payment.payment_date >= date_from
            )

        if date_to:
            query = query.where(
                Payment.payment_date <= date_to
            )

        return query

    async def create(
        self,
        *,
        project_id: str,
        amount,
        payment_type: str,
        payment_status: str,
        payment_date: date | None,
        description: str | None,
    ) -> Payment:
        payment = Payment(
            project_id=project_id,
            amount=amount,
            type=payment_type,
            status=payment_status,
            payment_date=payment_date,
            description=description,
        )

        self.db.add(payment)

        await self.db.flush()
        await self.db.refresh(payment)

        return payment

    async def delete(
        self,
        payment: Payment,
    ) -> None:
        await self.db.delete(payment)
        await self.db.flush()
