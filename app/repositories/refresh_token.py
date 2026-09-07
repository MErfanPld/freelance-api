from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: str,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
        )

        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)

        return token

    async def revoke(
        self,
        token: RefreshToken,
    ) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
