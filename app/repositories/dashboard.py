from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.note import Note
from app.models.payment import Payment
from app.models.project import Project
from app.models.task import Task


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_projects(
        self,
        user_id: str,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.user_id == user_id
            )
        )

        return result.scalar_one()

    async def count_projects_by_status(
        self,
        user_id: str,
        status: str,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.user_id == user_id,
                Project.status == status,
            )
        )

        return result.scalar_one()

    async def count_clients(
        self,
        user_id: str,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Client.id)).where(
                Client.user_id == user_id
            )
        )

        return result.scalar_one()

    async def count_tasks(
        self,
        user_id: str,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Task.id))
            .join(Project, Task.project_id == Project.id)
            .where(Project.user_id == user_id)
        )

        return result.scalar_one()

    async def count_tasks_by_status(
        self,
        user_id: str,
        status: str,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Task.id))
            .join(Project, Task.project_id == Project.id)
            .where(
                Project.user_id == user_id,
                Task.status == status,
            )
        )

        return result.scalar_one()

    async def payment_totals(
        self,
        user_id: str,
    ) -> tuple[Decimal, Decimal]:
        result = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.type == "income"
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ).filter(
                        Payment.type == "expense"
                    ),
                    0,
                ),
            )
            .join(
                Project,
                Payment.project_id == Project.id,
            )
            .where(Project.user_id == user_id)
        )

        income, expense = result.one()

        return (
            Decimal(str(income)),
            Decimal(str(expense)),
        )

    async def monthly_revenue(
        self,
        user_id: str,
        year: int,
        month: int,
    ) -> Decimal:
        result = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                )
            )
            .join(
                Project,
                Payment.project_id == Project.id,
            )
            .where(
                Project.user_id == user_id,
                Payment.type == "income",
                Payment.status == "paid",
                Payment.payment_date.is_not(None),
                func.strftime(
                    "%Y",
                    Payment.payment_date,
                )
                == str(year),
                func.strftime(
                    "%m",
                    Payment.payment_date,
                )
                == f"{month:02d}",
            )
        )

        value = result.scalar_one()

        return Decimal(str(value))

    async def recent_projects(
        self,
        user_id: str,
        limit: int,
    ):
        result = await self.db.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def recent_tasks(
        self,
        user_id: str,
        limit: int,
    ):
        result = await self.db.execute(
            select(Task)
            .join(Project, Task.project_id == Project.id)
            .where(Project.user_id == user_id)
            .order_by(Task.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def recent_payments(
        self,
        user_id: str,
        limit: int,
    ):
        result = await self.db.execute(
            select(Payment)
            .join(Project, Payment.project_id == Project.id)
            .where(Project.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def recent_notes(
        self,
        user_id: str,
        limit: int,
    ):
        result = await self.db.execute(
            select(Note)
            .join(Project, Note.project_id == Project.id)
            .where(Project.user_id == user_id)
            .order_by(Note.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())
