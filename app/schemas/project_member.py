from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MemberRole = Literal["owner", "member"]
MemberStatus = Literal[
    "pending",
    "active",
    "rejected",
    "left",
    "removed",
]


class ProjectInviteCreate(BaseModel):
    user_id: str = Field(min_length=36, max_length=36)
    role: MemberRole = "member"


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    user_id: str
    role: str
    status: str
    invited_by_id: str | None
    invited_at: datetime | None
    joined_at: datetime | None
    first_name: str | None = None
    last_name: str | None = None


class ProjectMemberListResponse(BaseModel):
    items: list[ProjectMemberResponse]
    total: int


class PublicUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str


class ProjectSummaryResponse(BaseModel):
    id: str
    name: str
    status: str
    member_count: int
    task_count: int
    completed_task_count: int
    total_income: str
    total_expense: str
    net_balance: str
    budget: str | None
    remaining_budget: str | None


class PendingInvitationResponse(BaseModel):
    """Invitation awaiting the current user's accept/reject."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    project_name: str | None = None
    user_id: str
    role: str
    status: str
    invited_by_id: str | None = None
    invited_by_first_name: str | None = None
    invited_by_last_name: str | None = None
    invited_at: datetime | None = None


class PendingInvitationListResponse(BaseModel):
    items: list[PendingInvitationResponse]
    total: int
