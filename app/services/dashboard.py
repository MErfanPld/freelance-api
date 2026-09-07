from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard import DashboardRepository


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.dashboard = DashboardRepository(db)

    async def get_summary(
        self,
        user_id: str,
    ):
        now = datetime.now(timezone.utc)

        (
            total_projects,
            active_projects,
            completed_projects,
            total_clients,
            total_tasks,
            pending_tasks,
            completed_tasks,
            payment_totals,
            monthly_revenue,
        ) = await self._load_summary_data(
            user_id,
            now,
        )

        total_income, total_expense = payment_totals

        recent_activity = await self._build_recent_activity(
            user_id
        )

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_clients": total_clients,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "total_income": total_income,
            "total_expense": total_expense,
            "profit": total_income - total_expense,
            "monthly_revenue": monthly_revenue,
            "recent_activity": recent_activity,
        }

    async def _load_summary_data(
        self,
        user_id: str,
        now: datetime,
    ):
        total_projects = (
            await self.dashboard.count_projects(
                user_id
            )
        )

        active_projects = (
            await self.dashboard.count_projects_by_status(
                user_id,
                "in_progress",
            )
        )

        completed_projects = (
            await self.dashboard.count_projects_by_status(
                user_id,
                "completed",
            )
        )

        total_clients = (
            await self.dashboard.count_clients(
                user_id
            )
        )

        total_tasks = (
            await self.dashboard.count_tasks(
                user_id
            )
        )

        pending_tasks = (
            await self.dashboard.count_tasks_by_status(
                user_id,
                "todo",
            )
        )

        completed_tasks = (
            await self.dashboard.count_tasks_by_status(
                user_id,
                "done",
            )
        )

        payment_totals = (
            await self.dashboard.payment_totals(
                user_id
            )
        )

        monthly_revenue = (
            await self.dashboard.monthly_revenue(
                user_id,
                now.year,
                now.month,
            )
        )

        return (
            total_projects,
            active_projects,
            completed_projects,
            total_clients,
            total_tasks,
            pending_tasks,
            completed_tasks,
            payment_totals,
            monthly_revenue,
        )

    async def _build_recent_activity(
        self,
        user_id: str,
    ) -> list[dict]:
        projects = await self.dashboard.recent_projects(
            user_id,
            5,
        )

        tasks = await self.dashboard.recent_tasks(
            user_id,
            5,
        )

        payments = await self.dashboard.recent_payments(
            user_id,
            5,
        )

        notes = await self.dashboard.recent_notes(
            user_id,
            5,
        )

        activities = []

        for project in projects:
            activities.append(
                {
                    "type": "project_created",
                    "title": "Project created",
                    "description": project.name,
                    "created_at": project.created_at,
                }
            )

        for task in tasks:
            activity_type = (
                "task_completed"
                if task.status == "done"
                else "task_created"
            )

            activities.append(
                {
                    "type": activity_type,
                    "title": (
                        "Task completed"
                        if task.status == "done"
                        else "Task created"
                    ),
                    "description": task.title,
                    "created_at": task.created_at,
                }
            )

        for payment in payments:
            activities.append(
                {
                    "type": "payment_added",
                    "title": "Payment added",
                    "description": str(
                        payment.amount
                    ),
                    "created_at": payment.created_at,
                }
            )

        for note in notes:
            activities.append(
                {
                    "type": "note_created",
                    "title": "Note created",
                    "description": note.title,
                    "created_at": note.created_at,
                }
            )

        activities.sort(
            key=lambda item: item["created_at"],
            reverse=True,
        )

        return activities[:10]
