from operator import index
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine

import os

raw_db_url = os.getenv("POSTGRES_URL")

DATABASE_URL = raw_db_url
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Async engine for Postgres
engine = create_async_engine(DATABASE_URL, future=True, echo=False)

Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, index=True)
    name = Column(String, index=True)
    status = Column(String)
    description = Column(String)
    severity = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class Services(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    resource_id = Column(String)
    resource_type = Column(String)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_checked = Column(DateTime(timezone=True), nullable=True)
    status = Column(String)
    is_active = Column(Boolean, default=True)


class RemediationLogs(Base):
    __tablename__ = "remediation_logs"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer)
    status = Column(String)
    error_message = Column(String)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    time = Column(DateTime(timezone=True), nullable=True)
    action = Column(String)
    details = Column(String)


class Configurations(Base):
    __tablename__ = "configurations"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def init_db():
    """Create database tables asynchronously. Call this at application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
