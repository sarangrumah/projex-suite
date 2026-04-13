"""Async SQLAlchemy engine and session factory with schema-per-tenant support."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.db_echo,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session. Tenant search_path is set by middleware."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def set_tenant_schema(session: AsyncSession, tenant_slug: str) -> None:
    """Set the PostgreSQL search_path to the tenant's schema."""
    schema = f"tenant_{tenant_slug}"
    await session.execute(text(f"SET search_path TO {schema}, public"))


async def get_all_tenant_schemas(session: AsyncSession) -> list[str]:
    """Return all tenant schema names from the database."""
    result = await session.execute(
        text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'")
    )
    return [row[0] for row in result.fetchall()]


async def create_tenant_schema(session: AsyncSession, tenant_slug: str) -> str:
    """Create a new tenant schema from template."""
    schema = f"tenant_{tenant_slug}"
    await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    await session.commit()
    return schema
