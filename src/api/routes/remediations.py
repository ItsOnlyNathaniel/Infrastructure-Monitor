# Triggers and retrieves remediation actions for incidents
#Imports
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from datetime import datetime
from src.services.RemediationService import RemediationService
from src.core.database import get_db


router = APIRouter()

#Class Definitions
class RemediationResponse(BaseModel): # Structure of the remediation response
    id: int
    incident_id: int
    time: datetime
    actions: List[str] = []
    status: str

class RemediationRequest(BaseModel): # Structure of the remediation request
    incident_id: int
    status: str
    message: str


@router.post("/trigger", response_model=RemediationResponse, status_code=200)
async def trigger_remediation(request: RemediationRequest, db: AsyncSession = Depends(get_db)):
    service = RemediationService(db)

    remediation_id = await service.create_remediation(
        resource_id = request.resource.id,
        resource_type = request.resource.type,
        issue_type = request.issue_type
    )

    #Wait for request approval to execute otherwise wait for approval
    #if approved status = "executing" + message
    #else status = "pending approval" + message

    return remediationResponse(id, status, message)

@router.get("/{remediation_id}")
async def get_remediation_status(remediation_id: str, db: AsyncSession = Depends(get_db)):
    service = RemediationService(db)
    status = await service.get_remediation_status(remediation_id)
    return status