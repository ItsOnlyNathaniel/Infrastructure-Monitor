# Imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid
from datetime import datetime
from src.database.models import Incident, RemediationLogs, Services
from src.monitors.ec2Monitor import EC2Monitor
from src.monitors.ecsMonitor import ECSMonitor

logger = logging.getLogger(__name__)

class RemediationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.remediators = {
            "ec2": EC2Monitor(),
            "ecs": ECSMonitor(),
        }


    async def get_remediation_status(self, remediation_id: int):
        status_search = select(RemediationLogs).where(RemediationLogs.id == int(remediation_id))
        status_result = await self.db.execute(status_search)
        status = status_result.scalar_one_or_none()

        if not status:
            raise ValueError(f"Remediation not found: {remediation_id}")
        return {
            "remediation_id": str(status.id),
            "status": status.status,
            "action": status.action,
            "started_at": status.started_at.isoformat() if status.started_at else None,
            "completed_at": status.completed_at.isoformat() if status.completed_at else None,
            "error_message": status.error_message
        }
          

    async def create_remediation(self, resource_id: str, resource_type: str, issue_type: str):
        remediation_id = str(uuid.uuid4()) # New remediation record

        # Find the service
        service_search = select(Services).where(Services.resource_id == resource_id)
        service_result = await self.db.execute(service_search)
        service = service_result.scalar_one_or_none
        # If isn't found
        if not service:
            raise ValueError(f"Service not found: {resource_id}")

        # Find the incident
        incident_search = select(Incident).where(Incident.service_id == service.id, Incident.status =="open").order_by(Incident.created_at.desc())
        incident_result = await self.db.execute(incident_search)
        incident = incident_result.scalar_one_or_none

        #Create a remediation log
        remediation = RemediationLogs(
            incident_id = incident.id if incident else None,
            service_id = service.id,
            action = issue_type,
            status = "pending"
        )
        self.db.add(remediation)
        await self.db.commit()
        await self.db.refresh(remediation)

        logger.info("Created remediation %s for %s: %s ", remediation.id, resource_type, resource_id)


    async def execute_remediation(self, remediation_id: str):

        remediation_search = select(RemediationLogs).where(RemediationLogs.id == int(remediation_id))
        remediation_result = await self.db.execute(remediation_search)
        remediation = remediation_result.scalar_one_or_none()
        remediation.status = "executing"
        await self.db.commit()

        try:
            service_search = select(Services).where(Services.id == remediation.service_id)
            service_result = await self.db.execute(service_search)
            service = service_result.scalar_one()

            remediator = self.remediators.get(service.resource_type.lower())
            if not remediator:
                raise ValueError(f"No rememdiator for type {service.resource_type}")

            await remediator.remediate(service.resource_id, remediation.action)

            remediation.status = "completed"
            remediation.completed_at = datetime.utcnow()
            await self.db.commit()

            logger.info("Executed remediation %s successfully", remediation.id)

        except Exception as e:
            logger.error("Remediation %s failed: %s", remediation_id, str(e))
            remediation.status = "failed"
            remediation.error_message = str(e)
            remediation.completed_at = datetime.utcnow()
            await self.db.commit()
            raise
