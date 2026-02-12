# Endpoints for managing incidents
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.core.database import get_db
from src.services.incident_service import IncidentService

router = APIRouter()

class IncidentRequest(BaseModel):
    incident_id: int
    resource_type: str
    status: str


class IncidentResponse(BaseModel):
    incident_id: int
    resource_type: str
    status: str

#Endpoints
@router.get("/incidents", response_model=IncidentResponse, status_code = 200)
async def get_all_incidents(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)
): # list all incidents
    service = IncidentService(db)

    try:
        incidents = await service.list_incidents()
        if incidents == "ignore":
            raise HTTPException(status_code=404, detail="No incidents found")
        return IncidentResponse(**incidents)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve incidents: {str(e)}") from e

@router.get("/incidents/{incident_id}", response_model=IncidentResponse, status_code = 200)
async def get_incident(incident_id: int, db:AsyncSession = Depends(get_db)):
    service = IncidentService(db)

    try:
        incident = await service.get_incident(incident_id)
        if incident is None:
            raise HTTPException(status_code=404, detail=f"Incident with id {incident_id} not found")
        return IncidentResponse(**incident)

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve incident: {str(e)}"
        ) from e

@router.patch("/incidents/{incident_id}", response_model=IncidentResponse, status_code=200)
async def update_incident(incident_id: int, status: str, db: AsyncSession = Depends(get_db)):
    service = IncidentService(db)

    try:
        await service.update_incident(incident_id, status)
        return IncidentResponse(status="updated")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update incident: {str(e)}") from e
