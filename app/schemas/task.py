from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TaskStatus = Literal[
    "todo",
    "in_progress",
    "done",
    "cancelled",
]

TaskPriority = Literal[
    "low",
    "medium",
    "high",
]


class TaskCreate(BaseModel):
    project_id: str
    assignee_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    estimated_hours: float | None = Field(
        default=None,
        ge=0,
    )
    actual_hours: float | None = Field(
        default=None,
        ge=0,
    )
    due_date: date | None = None


class TaskUpdate(BaseModel):
    assignee_id: str | None = None
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    estimated_hours: float | None = Field(
        default=None,
        ge=0,
    )
    actual_hours: float | None = Field(
        default=None,
        ge=0,
    )
    due_date: date | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    description: str | None
    status: str
    priority: str
    estimated_hours: float | None
    actual_hours: float | None
    due_date: date | None
    created_by_id: str | None = None
    assignee_id: str | None = None


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    pages: int
