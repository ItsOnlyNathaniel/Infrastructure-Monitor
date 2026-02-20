# Imports
import asyncio
import datetime
import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.redis_client import redis_client
from src.database.models import Incident, RemediationLogs, Services
from src.services.monitor_service import MonitorService

logger = logging.getLogger(__name__)

class VerificationService():
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def verify_remediation(self,remediation_id: str, delay: int):

        remediation_search = select(RemediationLogs).where(RemediationLogs.id == (remediation_id))
        remediation_results = await self.db.execute(remediation_search)
        remediation= remediation_results.scalar_one_or_none()
        if not remediation:
            raise ValueError(f"Remediation not found: {remediation_id}")

        service_search = select(Services).where(Services.id == remediation.service_id)
        service_result = await self.db.execute(service_search)
        service: Optional[Services] = service_result.scalar_one_or_none()
        if not service:
            raise ValueError(f"Service not found for remediation: {remediation_id}")
        if not service.resource_id or not service.resource_type:
            raise ValueError(f"Service {service.id} missing resource_id/resource_type")

        # Load incident (best-effort; remediation may exist without an incident_id)
        incident: Optional[Incident] = None
        if remediation.incident_id is not None:
            incident_search = select(Incident).where(Incident.id == remediation.incident_id)
            incident_result = await self.db.execute(incident_search)
            incident = incident_result.scalar_one_or_none()

        remediation.status = "verifying"
        await self.db.commit()

        monitor_service = MonitorService(self.db)
        monitor: Any | None = monitor_service.monitors.get(service.resource_type.lower())
        if not monitor:
            raise ValueError(f"No monitor found for resource type: {service.resource_type}")

        # "Before" snapshot from cache; if absent, fall back to DB/incident snapshot.
        before_health: Optional[dict] = None
        try:
            cache_key = f"health_check_{service.resource_type}_{service.resource_id}"
            before_health = await redis_client.get(cache_key)
        except Exception:
            logger.exception(
                "Failed to read cached health for verification",
                extra={"resource_type": service.resource_type, "resource_id": service.resource_id},
            )

        if not isinstance(before_health, dict):
            before_health = {
                "resource_id": service.resource_id,
                "resource_type": service.resource_type,
                "status": (service.status if isinstance(service.status, str) else "unknown"),
                "issues": ([incident.description] if incident and incident.description else []),
            }

        after_health: dict = await monitor.health_check(service.resource_id)
        after_status = after_health.get("status")

        verified_success = after_status == "healthy"

        remediation.verification_timestamp = datetime.datetime.now(datetime.timezone.utc)
        remediation.verification_status = (
            "verified_success" if verified_success else "verified_failure"
        )
        remediation.status = "verified"
        remediation.verification_details = {
            "delay_seconds": delay,
            "before": before_health,
            "after": after_health,
            "comparison": {
                "before_status": before_health.get("status"),
                "after_status": after_status,
                "improved": (before_health.get("status") != after_status),
            },
        }

        if incident:
            if verified_success:
                incident.status = "resolved"
                incident.resolved_at = datetime.datetime.now(datetime.timezone.utc)
            else:
                incident.status = "escalated"
                incident.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.db.commit()
