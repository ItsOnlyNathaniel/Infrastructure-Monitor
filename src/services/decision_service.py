import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Incident, Services, RemediationRules, RemediationLogs
from src.core.redis_client import redis_client
from typing import Optional
logger = logging.getLogger(__name__)

class DecisionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_incident_info(self, incident_id: Optional[int] = None, is_active: Optional[bool] = None):
        # Fetch incident data
        incident_search = select(Incident).where(Incident.id == incident_id)
        incident_result = await self.db.execute(incident_search)
        incident = incident_result.scalar_one_or_none()
        if not incident:
            logger.warning("Incident %s not found", incident_id)
            return "ignore"

        # Fetch service data using service_id from incident
        service_search = select(Services).where(Services.id == incident.service_id)
        service_result = await self.db.execute(service_search)
        service = service_result.scalar_one_or_none()
        if not service:
            logger.warning("Service %s not found for incident %s", incident.service_id, incident_id)
            return "ignore"

        # Get service health data from cache or use service status
        health_data = None
        if service.resource_type and service.resource_id:
            cache_key = f"health_check_{service.resource_type}_{service.resource_id}"
            health_data = await redis_client.get(cache_key)
        if not health_data:
            health_data = {
                "status": service.status,
                "issues": [incident.description] if incident.description else []
            }

        rule = await self.fetch_remediation_rule(
            resource_type = service.resource_type,
            issue_type = incident.description,
        )

        if not rule:
            logger.info("No matching remediation rule for incident %s - ignoring", incident_id)
            return "ignore"
        else:
            return rule


# Find remediation rule matching the incident criteria
    async def fetch_remediation_rule(self, resource_type: str, issue_type: str):
        rule_search = select(RemediationRules).where(
            RemediationRules.resource_type == resource_type,
            RemediationRules.issue_type == issue_type,
            RemediationRules.is_active == True,
        ).order_by(RemediationRules.priority.desc())

        result = await self.db.execute(rule_search)
        rules = result.scalars().all()

        for rule in rules:
            if rule.attempt_count < rule.max_attempts:
                logger.info("Matching remediation rule %s found for resource_type %s and issue_type %s",
                rule.id, resource_type, issue_type)
                return rule
            else:
                logger.info("No remediation rule found for resource_type %s and issue_type %s within attempt limits",
                resource_type, issue_type)


    async def attempt_count(self, incident: Incident, rule: RemediationRules):
        query = (
            select(RemediationLogs).where(
                RemediationLogs.incident_id == incident.id,
                RemediationLogs.status == "failed"
            )
        )
        result = await self.db.execute(query)
        prior_fails = result.scalars().all()

        if prior_fails < rule.max_attempts:
            logger.info("Max attempts exceeded")
            return False
        else:
            logger.info("Incident has %s prior attempts at remediation")
            return True

#TODO: Add filtering to evaluate conditions against incident context
