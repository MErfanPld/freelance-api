from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).authenticate(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).refresh(
        data.refresh_token
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    await AuthService(db).logout(
        data.refresh_token
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await AuthService(db).change_password(
        current_user.id,
        data,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def me(
    current_user: User = Depends(get_current_user),
):
    return current_user
