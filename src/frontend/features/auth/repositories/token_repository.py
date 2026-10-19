import hashlib
import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.frontend.features.auth.models import RefreshToken


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: uuid.UUID, token: str, expires_at: datetime) -> RefreshToken:
        db_token = RefreshToken(user_id=user_id, token_hash=hash_refresh_token(token), expires_at=expires_at)
        self.session.add(db_token)
        await self.session.flush()
        await self.session.refresh(db_token)
        return db_token

    async def get_by_token(self, token: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(token))
        )
        return result.scalar_one_or_none()

    async def rotate(self, *, user_id: uuid.UUID, old_token: str, new_token: str, expires_at: datetime) -> bool:
        """Claim the old row and insert its successor in the caller's transaction.

        PostgreSQL serializes competing DELETEs on this row; only one caller
        receives an id and may insert a successor. No commit occurs here.
        """
        result = await self.session.execute(
            delete(RefreshToken)
            .where(RefreshToken.token_hash == hash_refresh_token(old_token), RefreshToken.user_id == user_id)
            .returning(RefreshToken.id)
            .execution_options(synchronize_session=False)
        )
        if result.scalar_one_or_none() is None:
            return False
        await self.create(user_id=user_id, token=new_token, expires_at=expires_at)
        return True

    async def delete(self, token: str) -> None:
        await self.session.execute(delete(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(token)))

    async def delete_all_for_user(self, user_id: uuid.UUID) -> None:
        await self.session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
