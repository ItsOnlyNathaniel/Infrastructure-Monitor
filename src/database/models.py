from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import create_async_engine
from src.core.database import Base, engine, database_url


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, index=True)
    name = Column(String, index=True)
    issue_type = Column(String, nullable = True)
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
    service_id = Column(Integer)
    status = Column(String)
    error_message = Column(String)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)
    action = Column(String)
    details = Column(String)


class RemediationRules(Base):
    __tablename__ = "remediation_rules"
    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String, index=True)
    issue_type = Column(String)
    description = Column(String, nullable=True)
    conditions = Column(JSON)
    action = Column(String)
    is_active = Column(Boolean, default=True)
    auto_execute = Column(Boolean, default=False)
    priority = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)


async def init_db():
    # Create database tables asynchronously.
    # Called at application startup.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
