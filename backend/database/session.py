from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.config import db_settings
from backend.database.base import Base


engine = create_async_engine(
    url=db_settings.POSTGRES_URL,
    echo=db_settings.DEBUG,
    pool_pre_ping=True,
)

ASYNCSESSION_LOCAL = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    async with ASYNCSESSION_LOCAL() as session:
        yield session


async def create_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
