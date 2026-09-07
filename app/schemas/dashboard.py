from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


ActivityType = Literal[
    "project_created",
    "task_created",
    "task_completed",
    "payment_added",
    "note_created",
]


class RecentActivity(BaseModel):
    type: ActivityType
    title: str
    description: str | None = None
    created_at: datetime


class DashboardSummaryResponse(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int

    total_clients: int

    total_tasks: int
    pending_tasks: int
    completed_tasks: int

    total_income: Decimal
    total_expense: Decimal
    profit: Decimal

    monthly_revenue: Decimal

    recent_activity: list[RecentActivity]
