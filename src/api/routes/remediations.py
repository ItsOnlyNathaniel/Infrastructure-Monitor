# Triggers and retrieves remediation actions for incidents
# Imports
from email import message
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import datetime
from src.services.RemediationService import RemediationService
from src.core.database import get_db

router = APIRouter()

# Class Definitions
class RemediationResponse(BaseModel): # Structure of the remediation response
    remdiation_id: int
    status: str
    action: str
    resource_id: str
    completed_at: Optional[datetime.datetime] = None
    message: Optional[str] = None

class RemediationRequest(BaseModel): # Structure of the remediation request
    resource_id: str
    resource_type: str
    issue_type: str

# Endpoints
@router.post("/create", response_model=RemediationResponse, status_code=201)
async def create_remediation(request: RemediationRequest, db: AsyncSession = Depends(get_db)):
    service = RemediationService(db)

    try:
        remediation_id = await service.create_remediation(
            resource_id = request.resource_id,
            resource_type = request.resource_type,
            issue_type = request.issue_type
        )

        status = await service.get_remediation_status(remediation_id)

        return RemediationResponse(
            remdiation_id = remediation_id,
            status = status['status'],
            action = status['action'],
            resource_id = request.resource_id,
            completed_at = status['completed_at'],
            message = "Remediation triggered successfully"
        )

    except ValueError as ve:
        raise HTTPException(status_code = 404, detail = str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Failed to create remediation: {str(e)}") from e


@router.post("/{remediation_id}/execute", response_model=RemediationResponse, status_code=200)
async def execute_remediation(request: RemediationResponse, db: AsyncSession = Depends(get_db)):
    remediation_id: str
    service = RemediationService(db)

    try:
        await service.execute_remediation(remediation_id)
        status = await service.get_remediation_status(remediation_id)

        return RemediationResponse(
            remdiation_id = status["remediation_id"],
            status = status['status'],
            action = status['action'],
            resource_id = request.resource_id,
            completed_at = status['completed_at'],
            message = status.get("error_message"))

    except ValueError as ve:
        raise HTTPException(status_code = 404, detail = str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Failed to execute remediation: {str(e)}") from e


@router.get("/{remediation_id}/", response_model = RemediationResponse, status_code=200)
async def get_remediation_status(remediation_id: str, db: AsyncSession = Depends(get_db)):
    service = RemediationService(db)

    try:
        status = await service.get_remediation_status(remediation_id)

        return RemediationResponse(
            remdiation_id = status["remediation_id"],
            status = status['status'],
            action = status['action'],
            resource_id = status['resource_id'],
            completed_at = status['completed_at'],
            message = status.get("error_message"))

    except ValueError as ve:
        raise HTTPException(status_code = 404, detail = str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Failed to get remediation status: {str(e)}") from e

# TODO: Add endpoints which accept or reject remediation actions
