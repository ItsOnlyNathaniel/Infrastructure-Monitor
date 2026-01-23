import asyncio
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select

from src.core.config import settings
from src.core.database import AsyncSessionLocal, engine
from src.core.redis_client import RedisClient, redis_client
from src.database.models import Incident, Services
from src.services.DecisionService import DecisionService
from src.services.RemediationService import RemediationService

logger = logging.getLogger(__name__)


class RemediationWorker:
    def __init__(self, *, redis = redis_client, poll_interval_seconds = settings.HEALTH_CHECK_INTERVAL, max_concurrency = 5):
        self.redis = redis
        self.poll_interval_seconds = poll_interval_seconds
        self._shutdown_event: asyncio.Event = asyncio.Event()
        self._started: bool = False

    async def start(self) -> None:
        if self._started:
            return
        await self.redis.connect()
        self._started = True
        logger.info("RemediationWorker started")

    async def shutdown(self, reason: str = "shutdown") -> None:
        if self._shutdown_event.is_set():
            return
        logger.info("RemediationWorker shutting down", extra={"reason": reason})
        self._shutdown_event.set()

        try:
            await self.redis.disconnect()
        except Exception:
            logger.exception("Failed to disconnect Redis cleanly")

        try:
            await engine.dispose()
        except Exception:
            logger.exception("Failed to dispose DB engine cleanly")

        logger.info("RemediationWorker shutdown complete")

    async def get_open_incidents(self):
        async with AsyncSessionLocal() as db:
            incident_search = (
                select(Incident)
                .where(Incident.status == "Open")
                .order_by(Incident.created_at.asc())
            )

        incident_results = await db.execute(incident_search)
        incidents = incident_results.scalar().all()
        return [incident.id for incident in incidents]

    async def update_incident_status(
        self, incident_id: int, status: str, error_message: Optional[str] = None
    ):
        try:
            async with AsyncSessionLocal() as db:
                incident_search = select(Incident).where(Incident.id == incident_id)
                incident_result = await db.execute(incident_search)
                incident = incident_result.scalar_one_or_none()

                if not incident:
                    logger.warning(
                        "Incident %s not found for status update", incident_id
                    )
                    return

                incident.status = status

                # Set resolved_at if status indicates resolution
                if status in ("resolved", "closed", "completed"):
                    if incident.resolved_at is None:
                        incident.resolved_at = datetime.now()

                await db.commit()
                await db.refresh(incident)

                logger.info(
                    "Updated incident status",
                    extra={
                        "incident_id": incident_id,
                        "status": status,
                        "error_message": error_message,
                    },
                )

        except Exception as e:
            logger.error(
                "Failed to update incident status for %s: %s",
                incident_id,
                str(e),
                extra={"incident_id": incident_id, "status": status},
                exc_info=True,
            )

    async def process_incident(self, incident_id: int):
        try:
            async with AsyncSessionLocal() as db:
                decision_service = DecisionService(db)
                remediation_service = RemediationService(db)

                # Fetch incident
                incident_search = select(Incident).where(Incident.id == incident_id)
                incident_result = await db.execute(incident_search)
                incident = incident_result.scalar_one_or_none()

                if not incident:
                    logger.warning("Incident %s not found", incident_id)
                    return

                # Evaluate decision
                decision = await decision_service.fetch_incident_info(incident_id)

                if decision == "ignore":
                    logger.info(
                        "Skipping incident %s - decision: ignore",
                        incident_id,
                        extra={"incident_id": incident_id},
                    )
                    await self.update_incident_status(incident_id, "ignore", None)
                    return

                # Fetch service to get resource information
                service_search = select(Services).where(Services.id == incident.service_id)
                service_result = await db.execute(service_search)
                service = service_result.scalar_one_or_none()

                if not service:
                    logger.error(
                        "Service %s not found for incident %s",
                        incident.service_id,
                        incident_id,
                        extra={
                            "incident_id": incident_id,
                            "service_id": incident.service_id,
                        },
                    )
                    return

                if not service.resource_id or not service.resource_type:
                    logger.error(
                        "Service %s missing resource_id or resource_type for incident %s",
                        incident.service_id,
                        incident_id,
                        extra={
                            "incident_id": incident_id,
                            "service_id": incident.service_id,
                        },
                    )
                    return

                # Create remediation
                remediation_id = await remediation_service.create_remediation(
                    resource_id=service.resource_id,
                    resource_type=service.resource_type,
                    issue_type=incident.description or "unknown",
                )
                logger.info(
                    "Created remediation for incident",
                    extra={
                        "incident_id": incident_id,
                        "remediation_id": remediation_id,
                    },
                )

                # Execute remediation
                await remediation_service.execute_remediation(remediation_id)

                # Update incident status to in_progress on successful remediation start
                await self.update_incident_status(incident_id, "in_progress", None)

                logger.info(
                    "Successfully started remediation for incident",
                    extra={
                        "incident_id": incident_id,
                        "remediation_id": remediation_id,
                    },
                )

        except Exception as e:
            logger.error(
                "Error processing incident %s: %s",
                incident_id,
                str(e),
                extra={"incident_id": incident_id},
                exc_info=True
            )
            # Update incident status to indicate failure
            try:
                await self.update_incident_status(incident_id, "open", str(e))
            except Exception as update_error:
                logger.error(
                    "Failed to update incident status after error: %s",
                    str(update_error),
                    extra={"incident_id": incident_id}
                )
