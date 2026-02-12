from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
import datetime
import logging
from src.database.models import Incident, Services

logger = logging.getLogger(__name__)


class IncidentService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_incident(self, incident_id: int):
        incident_search = select(Incident).where(Incident.id == incident_id)
        incident_result = await self.db.execute(incident_search)
        incident = incident_result.scalar_one_or_none()

        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        return self._incident_to_dict(incident)

    async def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        resource_type: Optional[str] = None,
        service_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        List incidents with filters and pagination

        Returns:
            {
                "incidents": [...],
                "total": 100,
                "page": 1,
                "pages": 5
            }
        """
        incident_search = select(Incident)

        # Apply filters
        if status:
            incident_search = incident_search.where(Incident.status == status)
        if severity:
            incident_search = incident_search.where(Incident.severity == severity)
        if service_id:
            incident_search = incident_search.where(Incident.service_id == service_id)
        if resource_type:
            incident_search = incident_search.join(Services).where(Services.resource_type == resource_type)

        get_count = select(func.count()).select_from(incident_search.subquery())
        total_result = await self.db.execute(get_count)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * limit
        incident_search = incident_search.order_by(Incident.created_at.desc()).offset(offset).limit(limit)

        incident_result = await self.db.execute(incident_search)
        incidents = incident_result.scalars().all()

        return {
            "incidents": [self._incident_to_dict(inc) for inc in incidents],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,  # Ceiling division
        }

    async def update_incident(
        self,
        incident_id: int,
    ) -> Dict[str, Any]:
        incident_search = select(Incident).where(Incident.id == incident_id)
        incident_result = await self.db.execute(incident_search)
        incident = incident_result.scalar_one_or_none()

        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        # Update fields
        if incident.status is not None:
            incident.status = incident.status
            if incident.status in ("resolved", "closed"):
                incident.resolved_at = datetime.datetime.now()

        if incident.severity is not None:
            incident.severity = incident.severity

        if incident.description is not None:
            incident.description = incident.description

        incident.updated_at = datetime.datetime.now()

        await self.db.commit()
        await self.db.refresh(incident)

        logger.info("Updated incident %s", incident_id)
        return self._incident_to_dict(incident)

    async def close_incident(self, incident_id: int) -> Dict[str, Any]:

        incident_search = select(Incident).where(Incident.id == incident_id)
        incident_result = await self.db.execute(incident_search)
        incident = incident_result.scalar_one_or_none()

        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        incident.status = "resolved"
        incident.resolved_at = datetime.datetime.now()

        await self.db.commit()
        await self.db.refresh(incident)

        logger.info("Closed incident %s", incident_id)
        return self._incident_to_dict(incident)

    async def get_incident_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics about incidents"""
        # Count by status
        status_query = select(Incident.status, func.count(Incident.id)).group_by(
            Incident.status
        )

        status_result = await self.db.execute(status_query)
        status_counts = dict(status_result.all())

        # Count by severity (open only)
        severity_query = (
            select(Incident.severity, func.count(Incident.id))
            .where(Incident.status == "open")
            .group_by(Incident.severity)
        )

        severity_result = await self.db.execute(severity_query)
        severity_counts = dict(severity_result.all())

        return {
            "by_status": status_counts,
            "by_severity": severity_counts,
            "total_open": status_counts.get("open", 0),
        }

    def _incident_to_dict(self, incident: Incident) -> Dict[str, Any]:
        """Convert incident ORM object to dict"""
        return {
            "id": incident.id,
            "service_id": incident.service_id,
            "name": incident.name,
            "description": incident.description,
            "severity": incident.severity,
            "status": incident.status,
            "created_at": (incident.created_at.isoformat() if incident.created_at else None),
            "updated_at": (incident.updated_at.isoformat() if incident.updated_at else None),
            "resolved_at": (incident.resolved_at.isoformat() if incident.resolved_at else None),
        }
