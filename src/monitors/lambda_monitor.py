# Imports
import boto3
import logging
import datetime
from src.core.config import settings

logger = logging.getLogger(__name__)


class LambdaMonitor:
    def __init__(self):
        self.lambda_client = boto3.client(
            "lambda",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.ENDPOINT_URL
        )
        self.cloudwatch = boto3.client(
            "cloudwatch",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.ENDPOINT_URL
        )

    async def health_check(self, function_name: str):
        issues = []

        try:
            response = self.lambda_client.get_function(FunctionName=function_name)

            if not response:
                issues.append(f"Function {function_name} not found")
                status = "not_found"
            else:
                configuration = response["Configuration"]

                # Check function state
                state = configuration.get("State", "Unknown")
                if state != "Active":
                    issues.append(f"Function not active (state: {state})")

                # Check if function is published
                if configuration.get("State") == "Pending":
                    issues.append("Function is in pending state")

                # Check last modified time (optional - could indicate stale function)
                last_modified = configuration.get("LastModified", "")
                if last_modified:
                    # Could add logic here to check if function hasn't been updated in a while
                    pass

                status = "healthy" if not issues else "unhealthy"

        except self.lambda_client.exceptions.ResourceNotFoundException:
            issues.append(f"Function {function_name} not found")
            status = "not_found"
        except Exception as e:
            logger.error("Error checking Lambda function %s", function_name)
            status = "error"
            issues.append(str(e))

        return {
            "resource_id": function_name,
            "resource_type": "lambda",
            "status": status,
            "last_check": datetime.datetime.utcnow().isoformat(),
            "issues": issues,
        }
