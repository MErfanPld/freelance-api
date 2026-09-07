from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ProjectStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "cancelled",
]

ProjectPriority = Literal[
    "low",
    "medium",
    "high",
]


class ProjectCreate(BaseModel):
    client_id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: ProjectStatus = "pending"
    priority: ProjectPriority = "medium"
    start_date: date | None = None
    deadline: date | None = None
    budget: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date
            and self.deadline
            and self.deadline < self.start_date
        ):
            raise ValueError(
                "Deadline cannot be before start date"
            )

        return self


class ProjectUpdate(BaseModel):
    client_id: str | None = None
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    description: str | None = None
    status: ProjectStatus | None = None
    priority: ProjectPriority | None = None
    start_date: date | None = None
    deadline: date | None = None
    budget: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date
            and self.deadline
            and self.deadline < self.start_date
        ):
            raise ValueError(
                "Deadline cannot be before start date"
            )

        return self


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    client_id: str | None
    name: str
    description: str | None
    status: str
    priority: str
    start_date: date | None
    deadline: date | None
    budget: Decimal | None


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int
