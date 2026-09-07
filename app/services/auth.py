import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    async def register(
        self,
        data: RegisterRequest,
    ):
        existing_user = await self.users.get_by_email(
            data.email
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        user = await self.users.create(
            email=data.email,
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
        )

        await self.db.commit()

        return user

    async def authenticate(
        self,
        data: LoginRequest,
    ):
        user = await self.users.get_by_email(
            data.email
        )

        if not user or not verify_password(
            data.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return await self._create_token_pair(user.id)

    async def _create_token_pair(
        self,
        user_id: str,
    ) -> dict[str, str]:
        jti = str(uuid.uuid4())

        access_token = create_access_token(user_id)

        refresh_token = create_refresh_token(
            user_id,
            jti,
        )

        expires_at = datetime.now(
            timezone.utc
        ) + timedelta(
            days=settings.refresh_token_expire_days
        )

        await self.refresh_tokens.create(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh(
        self,
        refresh_token: str,
    ) -> dict[str, str]:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id or not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        stored_token = await self.refresh_tokens.get_by_jti(
            jti
        )

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found",
            )

        if stored_token.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        now = datetime.now(timezone.utc)

        expires_at = stored_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        user = await self.users.get_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not available",
            )

        # Rotation: revoke the old refresh token.
        await self.refresh_tokens.revoke(stored_token)

        tokens = await self._create_token_pair(user.id)

        await self.db.commit()

        return tokens

    async def logout(
        self,
        refresh_token: str,
    ) -> None:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        jti = payload.get("jti")

        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        stored_token = await self.refresh_tokens.get_by_jti(
            jti
        )

        if stored_token and stored_token.revoked_at is None:
            await self.refresh_tokens.revoke(stored_token)
            await self.db.commit()

    async def change_password(
        self,
        user_id: str,
        data: ChangePasswordRequest,
    ) -> None:
        user = await self.users.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not verify_password(
            data.current_password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different",
            )

        user.password_hash = hash_password(
            data.new_password
        )

        await self.db.commit()
