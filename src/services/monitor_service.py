# Imports
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from sqlalchemy import select
import datetime
import logging
from src.database.models import Services, Incident
from src.core.redis_client import redis_client
from src.monitors.ec2_monitor import EC2Monitor
from src.monitors.ecs_monitor import ECSMonitor
from src.monitors.lambda_monitor import LambdaMonitor
from src.monitors.rds_monitor import RDSMonitor
from src.monitors.alb_monitor import ALBMonitor

logger = logging.getLogger(__name__)


class MonitorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.monitors = {
            "ec2": EC2Monitor(),
            "ecs": ECSMonitor(),
            "rds": RDSMonitor(),
            "lambda":LambdaMonitor(),
            "alb": ALBMonitor(),
        }

    # Run health checks on specified resources
    async def check_resources(self, resource_type: str, resource_ids: List[str]):
        monitor: Any | None = self.monitors.get(resource_type.lower())
        if not monitor:
            raise ValueError(f"No monitor found for resource type: {resource_type}")

        results = []
        for resource_id in resource_ids:
            try:
                status = await monitor.health_check(resource_id)
                results.append(status)

                # Find the service
                service_search = select(Services).where(Services.resource_id == resource_id)
                service_result = await self.db.execute(service_search)
                service = service_result.scalar_one_or_none()

                # Update service status in database
                if service:
                    service.status = status
                    service.last_checked = datetime.datetime.now()
                    await self.db.commit()

                    # Create Incident where issues are present but not already identified
                    if status["issues"]:

                        incident = Incident(
                            service_id=service.id,
                            name=f"{resource_type} health check failed",
                            description=", ".join(status["issues"]),
                            severity="warning" if status["status"] == "unhealthy" else "critical",
                            status="open"
                        )
                        self.db.add(incident)
                        await self.db.commit()

                else:
                    logger.warning("Service not found in DB: %s", resource_id)

                # Cache the results
                cache_key = f"health_check_{resource_type}_{resource_id}"
                await redis_client.set(cache_key, status, ttl=300)

            # Catch exceptions and return error status
            except Exception as e:
                logger.error("Error checking health of %s %s: %s", resource_type, resource_id, str(e))
                results.append({
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "status": "error",
                    "issues": [str(e)],
                    "last_check": datetime.now()
                })


    # Run a fresh check or get cached results
    async def get_resource_status(self, resource_type: str, resource_id: str):
        results = await self.check_resources(resource_type, [resource_id])
        return results[0] if results else None


    async def get_all_services(self):
        service_search = select(Services)
        service_result = await self.db.execute(service_search)
        services = service_result.scalars().all()
        return [{
            "id": service.id,
            "name": service.name,
            "resource_id": service.resource_id,
            "resource_type": service.resource_type,
            "status": service.status,
            "last_checked": service.last_checked,
        } for service in services]
