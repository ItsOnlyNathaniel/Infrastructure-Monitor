#Imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

#  Database configuration
database_url = settings.postgres_url.replace("postgresql://", "postgresql+asyncpg://")
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