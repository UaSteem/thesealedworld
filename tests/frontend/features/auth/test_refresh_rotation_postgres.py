"""Real PostgreSQL rotation/failure proof, isolated from all configured databases.

Opt in with RUN_SITE_AUTH_POSTGRES=1. Reuses the disposable migration fixture.
"""

import asyncio
import hashlib
import os
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.frontend.features.auth.dto.token import Token
from src.frontend.features.auth.integrations.auth_persistence import AuthPersistence
from src.frontend.features.auth.models import RefreshToken
from src.frontend.features.auth.repositories.token_repository import TokenRepository
from src.frontend.features.auth.repositories.user_repository import UserRepository
from src.frontend.features.auth.services import site_auth_service as module
from tests.frontend.migrations.test_site_migrations_postgres import database, migrate, postgres, sql  # noqa: F401

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SITE_AUTH_POSTGRES") != "1", reason="explicit disposable PostgreSQL opt-in required"
)
OLD = "synthetic-old-refresh"
USER_ID = uuid.UUID("eaedc035-e892-4aa6-b438-ec63f01ff96b")


@pytest.fixture
def prepared(database, monkeypatch):  # noqa: F811 - imported reusable pytest fixture
    migrate(database)
    sql(
        database,
        "INSERT INTO site.auth_users (id,email,hashed_password,is_active,is_superuser,tester_status,referral_code) VALUES ($1,'rotation@example.test','synthetic-hash',true,false,'none','SEAL-ROTATION')",
        USER_ID,
    )
    sql(
        database,
        "INSERT INTO site.auth_refresh_tokens (user_id,token_hash,expires_at) VALUES ($1,$2,now()+interval '1 day')",
        USER_ID,
        hashlib.sha256(OLD.encode()).hexdigest(),
    )
    monkeypatch.setattr(module, "create_access_token", lambda **kwargs: "synthetic-access")
    monkeypatch.setattr(
        module, "settings", SimpleNamespace(access_token_expire_minutes=30, refresh_token_expire_days=30)
    )
    return database.replace("postgresql://", "postgresql+asyncpg://")


def persistence(session):
    return AuthPersistence(users=UserRepository(session), tokens=TokenRepository(session))


@pytest.mark.asyncio
async def test_concurrent_threshold_refresh_has_only_one_durable_successor(prepared):
    engine = create_async_engine(prepared)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    barrier = asyncio.Barrier(2)

    class ConcurrentPersistence(AuthPersistence):
        async def get_refresh_token(self, token):
            result = await super().get_refresh_token(token)
            await barrier.wait()
            return result

    async def refresh():
        async with maker() as session:
            port = ConcurrentPersistence(users=UserRepository(session), tokens=TokenRepository(session))
            return await module.AuthService(port).refresh_token(OLD)

    try:
        results = await asyncio.gather(refresh(), refresh(), return_exceptions=True)
        assert sum(isinstance(result, Token) for result in results) == 1
        assert sum(isinstance(result, module.RefreshTokenNotFoundError) for result in results) == 1
        async with maker() as session:
            rows = (await session.execute(select(RefreshToken))).scalars().all()
            assert len(rows) == 1 and rows[0].token_hash != hashlib.sha256(OLD.encode()).hexdigest()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["insert", "commit"])
async def test_failed_rotation_keeps_old_token_durable_and_session_usable(prepared, monkeypatch, failure):
    engine = create_async_engine(prepared)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    new = "synthetic-new-refresh"
    monkeypatch.setattr(module.secrets, "token_urlsafe", lambda size: new)
    digest = hashlib.sha256(new.encode()).hexdigest()
    try:
        async with engine.begin() as connection:
            if failure == "insert":
                await connection.execute(
                    text(
                        "INSERT INTO site.auth_refresh_tokens (user_id,token_hash,expires_at) VALUES (:uid,:digest,now()+interval '30 days')"
                    ),
                    {"uid": USER_ID, "digest": digest},
                )
            else:
                await connection.execute(
                    text(
                        "CREATE FUNCTION site.reject_refresh_commit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'synthetic deferred failure'; RETURN NEW; END $$"
                    )
                )
                await connection.execute(
                    text(
                        "CREATE CONSTRAINT TRIGGER reject_refresh_commit AFTER INSERT ON site.auth_refresh_tokens DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION site.reject_refresh_commit()"
                    )
                )
        async with maker() as session:
            with pytest.raises((IntegrityError, DBAPIError)):
                await module.AuthService(persistence(session)).refresh_token(OLD)
            # Rollback is part of the persistence operation, not a test repair.
            assert await TokenRepository(session).get_by_token(OLD) is not None
        async with maker() as verifier:
            hashes = set((await verifier.execute(select(RefreshToken.token_hash))).scalars())
            assert hashlib.sha256(OLD.encode()).hexdigest() in hashes
            assert len(hashes) == (2 if failure == "insert" else 1)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_lost_success_response_old_token_retry_rejected_without_second_rotation(prepared):
    engine = create_async_engine(prepared)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with maker() as session:
            result = await module.AuthService(persistence(session)).refresh_token(OLD)
        async with maker() as session:
            with pytest.raises(module.RefreshTokenNotFoundError):
                await module.AuthService(persistence(session)).refresh_token(OLD)
        async with maker() as session:
            result_again = await module.AuthService(persistence(session)).refresh_token(result.refresh_token)
            assert result_again.refresh_token == result.refresh_token
            assert len((await session.execute(select(RefreshToken))).scalars().all()) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_healthy_refresh_keeps_existing_token_and_expiry(prepared):
    engine = create_async_engine(prepared)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("UPDATE site.auth_refresh_tokens SET expires_at=now()+interval '20 days'"))
        async with maker() as session:
            before = await TokenRepository(session).get_by_token(OLD)
            expiry = before.expires_at
            result = await module.AuthService(persistence(session)).refresh_token(OLD)
            assert result.refresh_token == OLD
        async with maker() as session:
            rows = (await session.execute(select(RefreshToken))).scalars().all()
            assert len(rows) == 1 and rows[0].expires_at == expiry
    finally:
        await engine.dispose()
