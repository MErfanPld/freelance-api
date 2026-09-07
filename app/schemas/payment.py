from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


PaymentType = Literal[
    "income",
    "expense",
]

PaymentStatus = Literal[
    "paid",
    "unpaid",
]


class PaymentCreate(BaseModel):
    project_id: str
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
    )
    type: PaymentType
    status: PaymentStatus = "unpaid"
    payment_date: date | None = None
    description: str | None = None


class PaymentUpdate(BaseModel):
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
    )
    type: PaymentType | None = None
    status: PaymentStatus | None = None
    payment_date: date | None = None
    description: str | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    amount: Decimal
    type: str
    status: str
    payment_date: date | None
    description: str | None


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PaymentSummaryResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    total_paid: Decimal
    total_unpaid: Decimal
    profit: Decimal


class MonthlyPaymentSummary(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    total_paid: Decimal
    total_unpaid: Decimal
    profit: Decimal
