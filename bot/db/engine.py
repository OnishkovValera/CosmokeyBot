from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from bot.config import settings

class Database:
    def __init__(self):
        self.url = create_postgres_url()
        self._engine = create_async_engine(
            self.url,
            echo=False,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=10,
            max_overflow=5,
            pool_timeout=30,
        )
        self._session_factory = async_sessionmaker(bind=self._engine, expire_on_commit=False)

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory


def create_postgres_url() -> str:
    return (f"{settings.POSTGRES_DRIVER}://"
            f"{settings.POSTGRES_USER}:"
            f"{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_HOST}:"
            f"{settings.POSTGRES_PORT}/"
            f"{settings.POSTGRES_DB}")


db = Database()