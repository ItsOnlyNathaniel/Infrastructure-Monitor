# Replaces health.py for monitoring status of services. Based on model schema
#Imports
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from src.services.MonitorService import MonitorService 
from src.core.database import get_db

router = APIRouter()

#Class Definitions
class MonitorStatus(BaseModel): # Structure of the monitoring status response
    resource_id: str
    resource_type: str
    status: str
    last_check: str
    issues: List[str] = []

class MonitorRequest(BaseModel): # Structure of the monitoring request
    resource_type: str  # ec2, ecs, rds, etc
    resource_ids: List[str] = []


@router.post("/check", response_model=List[MonitorStatus], status_code=200)
async def run_health_check(request: MonitorRequest, db: AsyncSession = Depends(get_db)):
    pass
    service = MonitorService(db) # 
    health = await service.check_resources(request.resource_type, request.resource_ids) # Not complete
    return health


@router.get("/{resource_type}/{resource_id}", response_model=MonitorStatus, status_code=200)
async def get_resource_status(resource_type: str, resource_id: str, db : AsyncSession = get_db()):

    service = MonitorService(db)
    status = await service.get_resource_status(resource_type, resource_id)

    return status