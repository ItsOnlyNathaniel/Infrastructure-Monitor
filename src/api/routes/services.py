#Imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from src.services.monitor_service import MonitorService
from src.core.database import get_db

router = APIRouter()

# Class Definitions
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
    service = MonitorService(db)

    try:
        health = await service.check_resources(request.resource_type, request.resource_ids)
        return [MonitorStatus(**status) for status in health]

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run health check: {str(e)}") from e


@router.get("/{resource_type}/{resource_id}", response_model=MonitorStatus, status_code=200)
async def get_resource_status(resource_type: str, resource_id: str, db: AsyncSession = Depends(get_db)):
    service = MonitorService(db)

    try:
        status = await service.get_resource_status(resource_type, resource_id)
        return MonitorStatus(**status)

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resource status: {str(e)}") from e

@router.get("/services", response_model=List[MonitorStatus], status_code=200)
async def get_all_services(db: AsyncSession = Depends(get_db)):
    service = MonitorService(db)

    try:
        services = await service.get_all_services()
        return [MonitorStatus(**service) for service in services]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get all services: {str(e)}") from e
