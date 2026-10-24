from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    title: str
    message: str
    data: dict[str, Any] | None
    is_read: bool
    project_id: str | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    pages: int
    unread_count: int
