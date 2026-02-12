import asyncio
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select

from src.core.config import settings
from src.core.database import AsyncSessionLocal, engine
from src.core.redis_client import redis_client
from src.database.models import Incident, Services
from src.services.decision_service import DecisionService
from src.services.remediation_service import RemediationService

logger = logging.getLogger(__name__)


class RemediationWorker:
    #Note: Incident polling/processing is still WIP in this file. This class focuses on
    #initialization, DB/Redis resource management, and graceful shutdown handling.

    def __init__(self, *, redis = redis_client, poll_interval_seconds = settings.HEALTH_CHECK_INTERVAL, max_concurrency = 5):
        self.redis = redis
        self.poll_interval_seconds = poll_interval_seconds
        self.max_concurrency = max_concurrency
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

        try:
            async with AsyncSessionLocal() as db:
                incident_search = (
                    select(Incident)
                    .where(Incident.status == "open")
                    .order_by(Incident.created_at.asc())
                )
                incident_results = await db.execute(incident_search)
                incidents = incident_results.scalars().all()

            incident_ids = [incident.id for incident in incidents]

            logger.debug(
                "Fetched open incidents",
                extra={"count": len(incident_ids), "incident_ids": incident_ids},
            )
            return incident_ids

        except Exception as e:
            logger.error(
                "Failed to fetch open incidents: %s",
                str(e),
                exc_info=True,
            )
            return []

    async def update_incident_status(
        self, incident_id: int, status: str, error_message: Optional[str] = None):
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
                extra={"incident_id": incident_id, "status": status,"error_message": error_message},
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


    async def run(self):
        await self.start()
        logger.info("Worker started, polling every %ds", self.poll_interval_seconds)
        try:
            while not self._shutdown_event.is_set():
                try:
                    incidents = await self.get_open_incidents()
                    logger.info("Found %d open incidents", len(incidents))
                    for incident_id in incidents:
                        await self.process_incident(incident_id)
                except Exception as e:
                    logger.error("Error in worker loop: %s", str(e), exec_info=True)
                await asyncio.sleep(self.poll_interval_seconds)
        finally:
            await self.shutdown("Run loop exited")
