# Imports
import boto3
import logging
import datetime
import os

logger = logging.getLogger(__name__)


class RDSMonitor:
    def __init__(self):
        self.rds = boto3.client(
            "rds",
            region_name=os.getenv("AWS_DEFAULT_REGION"),
            endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
        )
        self.cloudwatch = boto3.client(
            "cloudwatch",
            region_name=os.getenv("AWS_DEFAULT_REGION"),
            endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
        )

    async def health_check(self, db_instance_identifier: str):
        issues = []

        try:
            response = self.rds.describe_db_instances(
                DBInstanceIdentifier=db_instance_identifier
            )

            if not response["DBInstances"]:
                issues.append(f"DB instance {db_instance_identifier} not found")
                status = "not_found"
            else:
                db_instance = response["DBInstances"][0]
                # Check DB instance status
                db_status = db_instance.get("DBInstanceStatus", "Unknown")
                if db_status != "available":
                    issues.append(f"DB instance not available (status: {db_status})")

                # Check if instance is in a maintenance state
                if db_status in ["maintenance", "modifying", "rebooting"]:
                    issues.append(f"DB instance is in {db_status} state")

                # Check storage
                allocated_storage = db_instance.get("AllocatedStorage", 0)
                max_allocated_storage = db_instance.get("MaxAllocatedStorage", 0)
                if (
                    max_allocated_storage > 0
                    and allocated_storage >= max_allocated_storage * 0.9
                ):
                    issues.append("DB instance storage is near maximum allocation")

                status = "healthy" if not issues else "unhealthy"

        except self.rds.exceptions.DBInstanceNotFoundFault:
            issues.append(f"DB instance {db_instance_identifier} not found")
            status = "not_found"
        except Exception as e:
            logger.error("Error checking RDS instance %s", db_instance_identifier)
            status = "error"
            issues.append(str(e))

        return {
            "resource_id": db_instance_identifier,
            "resource_type": "rds",
            "status": status,
            "last_check": datetime.datetime.utcnow().isoformat(),
            "issues": issues,
        }
