# Imports
import boto3
import logging
import datetime
from src.core.config import settings

logger = logging.getLogger(__name__)


class EC2Monitor:
    def __init__(self):
        self.ec2 = boto3.client(
            "ec2",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.ENDPOINT_URL,
        )
        self.cloudwatch = boto3.client(
            "cloudwatch",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.ENDPOINT_URL,
        )

    async def health_check(self, instance_id: str):
        issues = []

        try:
            response = self.ec2.describe_instance_status(
                InstanceIds=[instance_id], IncludeAllInstances=True
            )

            if not response["InstanceStatuses"]:
                issues.append(f"Instance {instance_id} not found")
                status = "not_found"
            else:
                instance_status = response["InstanceStatuses"][0]

                # Check instance state
                state = instance_status["InstanceState"]["Name"]
                if state != "running":
                    issues.append(f"Instance not running (state: {state})")

                # Check system status
                system_status = instance_status["SystemStatus"]["Status"]
                if system_status != "ok":
                    issues.append(f"System status check failed: {system_status}")

                # Check instance status
                inst_status = instance_status["InstanceStatus"]["Status"]
                if inst_status != "ok":
                    issues.append(f"Instance status check failed: {inst_status}")

                status = "healthy" if not issues else "unhealthy"

        except Exception as e:
            logger.error("Error checking EC2 service %s", instance_id)
            status = "error"
            issues.append(str(e))

        return {
            "resource_id": instance_id,
            "resource_type": "ec2",
            "status": status,
            "last_check": datetime.utcnow().isoformat(),
            "issues": issues,
        }
