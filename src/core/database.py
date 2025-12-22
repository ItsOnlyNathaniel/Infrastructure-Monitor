#Imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

#  Database configuration
raw_db_url = settings.postgres_url

database_url = raw_db_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
# Create async engine
engine = create_async_engine(database_url, echo=False, future=True)
# Create session factory
AsyncSessionLocal = sessionmaker(engine, class_ = AsyncSession, expire_on_commit=False)

Base = declarative_base()
# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
