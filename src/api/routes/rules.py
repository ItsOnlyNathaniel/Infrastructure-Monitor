# Endpoints for managing remediation rules
# Imports
import resource
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from src.services.RuleService import RuleService
from src.core.database import get_db

router = APIRouter()

# Class Definitions
class RuleResponse(BaseModel):
    """Structure of the rule response"""
    id: int
    resource_type: str
    issue_type: str
    description: Optional[str] = None
    conditions: Dict[str, Any] = {}
    action: str
    is_active: bool
    auto_execute: bool
    priority: int
    max_attempts: int

class RuleCreateRequest(BaseModel):
    """Structure of the rule creation request"""
    resource_type: str
    issue_type: str
    action: str
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: bool = True
    auto_execute: bool = False
    priority: int = 1
    max_attempts: int = 3

class RuleUpdateRequest(BaseModel):
    """Structure of the rule update request"""
    resource_type: Optional[str] = None
    issue_type: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    action: Optional[str] = None
    is_active: Optional[bool] = None
    auto_execute: Optional[bool] = None
    priority: Optional[int] = None
    max_attempts: Optional[int] = None

# Endpoints
@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule(request: RuleCreateRequest, db: AsyncSession = Depends(get_db)):
    service = RuleService(db)

    try:
        rule_id = await service.create_rule(
            resource_type=request.resource_type,
            issue_type=request.issue_type,
            action=request.action,
            description=request.description,
            conditions=request.conditions,
            is_active=request.is_active,
            auto_execute=request.auto_execute,
            priority=request.priority,
            max_attempts=request.max_attempts
        )

        return RuleResponse(
            rule_id = rule_id,
            resource_id = request.resource_id,
            issue_type = request.issue_type
        )

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create rule: {str(e)}"
        ) from e


@router.get("/", response_model=List[RuleResponse], status_code=200)
async def get_all_rules(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)):

    service = RuleService(db)

    try:
        rules = await service.get_all_rules(
            resource_type=resource_type,
            is_active=is_active
        )
        return [RuleResponse(**rule) for rule in rules]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve rules: {str(e)}"
        ) from e


@router.get("/{rule_id}", response_model=RuleResponse, status_code=200)
async def get_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific rule by ID"""
    service = RuleService(db)

    try:
        rule = await service.get_rule(rule_id)
        return RuleResponse(
            rule_id = rule_id,
            resource_type = request.resource_type,
            issue_type = request.issue_type,
            action = request.action,
            is_active = request.is_active,
        )

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve rule: {str(e)}"
        ) from e


@router.put("/{rule_id}", response_model=RuleResponse, status_code=200)
async def update_rule(rule_id: int, request: RuleUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Update an existing rule"""
    service = RuleService(db)

    try:
        rule = await service.update_rule(
            rule_id=rule_id,
            resource_type=request.resource_type,
            issue_type=request.issue_type,
            description=request.description,
            conditions=request.conditions,
            action=request.action,
            is_active=request.is_active,
            auto_execute=request.auto_execute,
            priority=request.priority,
            max_attempts=request.max_attempts
        )
        return RuleResponse(**rule)

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update rule: {str(e)}"
        ) from e


@router.patch("/{rule_id}/deactivate", response_model=RuleResponse, status_code=200)
async def deactivate_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """Deactivate a rule by setting is_active to False"""
    service = RuleService(db)

    try:
        rule = await service.toggle_rule_status(rule_id, is_active=False)
        return RuleResponse(**rule)

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deactivate rule: {str(e)}"
        ) from e
