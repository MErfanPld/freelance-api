from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.payment import (
    MonthlyPaymentSummary,
    PaymentCreate,
    PaymentListResponse,
    PaymentResponse,
    PaymentSummaryResponse,
    PaymentUpdate,
)
from app.services.payment import PaymentService


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentService(db).create(
        current_user.id,
        data,
    )


@router.get(
    "",
    response_model=PaymentListResponse,
)
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    project_id: str | None = None,
    payment_type: str | None = Query(
        None,
        alias="type",
    ),
    payment_status: str | None = Query(
        None,
        alias="status",
    ),
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentService(db).list(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        project_id=project_id,
        payment_type=payment_type,
        payment_status=payment_status,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/summary",
    response_model=PaymentSummaryResponse,
)
async def payment_summary(
    project_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentService(db).summary(
        user_id=current_user.id,
        project_id=project_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/monthly",
    response_model=MonthlyPaymentSummary,
)
async def monthly_payment_summary(
    year: int = Query(
        ...,
        ge=2000,
        le=2100,
    ),
    month: int = Query(
        ...,
        ge=1,
        le=12,
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentService(db).monthly_summary(
        user_id=current_user.id,
        year=year,
        month=month,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentService(db).get(
        payment_id,
        current_user.id,
    )


@router.patch(
    "/{payment_id}",
    response_model=PaymentResponse,
)
async def update_payment(
    payment_id: str,
    data: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentService(db).update(
        payment_id,
        current_user.id,
        data,
    )


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await PaymentService(db).delete(
        payment_id,
        current_user.id,
    )
