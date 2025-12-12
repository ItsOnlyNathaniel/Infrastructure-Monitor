from fastapi import FastAPI, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.orm import declarative_base

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index = True)
    name = Column(String, index=True)
    time = Column(DateTime)
    code: str

class Services(Base):
    __tablename__ = "Services"
    id = Column(Integer, primary_key=True, index = True)
    name = Column(String, index=True)
    code: str
    is_active = Column(Boolean, default=True)
    status = Column(String)

class RemediationLogs(Base):
    __tablename__ = "remediation_logs"
    id = Column(Integer, primary_key=True, index = True)
    name = Column(String, index=True)
    time = Column(DateTime)
    action = Column(String)

class Configurations(Base):
    __tablename__ = "configurations"
    id = Column(Integer, primary_key=True, index = True)
    name = Column(String, index=True)

# Create all tables    
Base.metadata.create_all(bind=engine)

async def create_db_and_tables():
    async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
