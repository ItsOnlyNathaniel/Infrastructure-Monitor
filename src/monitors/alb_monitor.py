import boto3
import logging
import datetime
from src.core.config import Settings

logger = logging.getLogger(__name__)


class ALBMonitor:
    """
    Health monitor for Application Load Balancers (ALB).

    The `load_balancer_arn_or_name` can be either the ALB ARN or its name.
    """

    def __init__(self):
        self.elbv2 = boto3.client(
            "elbv2",
            region_name=Settings.AWS_REGION,
            endpoint_url=Settings.ENDPOINT_URL
        )

    async def health_check(self, load_balancer_arn_or_name: str):
        """
        Perform a basic health check on an ALB.
        """
        issues = []

        try:
            # Resolve the load balancer by ARN or name
            if load_balancer_arn_or_name.startswith("arn:aws:elasticloadbalancing:"):
                response = self.elbv2.describe_load_balancers(
                    LoadBalancerArns=[load_balancer_arn_or_name]
                )
            else:
                response = self.elbv2.describe_load_balancers(
                    Names=[load_balancer_arn_or_name]
                )

            load_balancers = response.get("LoadBalancers", [])
            if not load_balancers:
                issues.append(f"Load balancer {load_balancer_arn_or_name} not found")
                status = "not_found"
            else:
                lb = load_balancers[0]

                # Check state
                state = lb.get("State", {}).get("Code", "unknown")
                if state != "active":
                    issues.append(f"ALB not active (state: {state})")

                # Basic scheme / type sanity
                lb_type = lb.get("Type", "unknown")
                if lb_type != "application":
                    issues.append(f"Load balancer is not of type 'application' (type: {lb_type})")

                status = "healthy" if not issues else "unhealthy"

        except self.elbv2.exceptions.LoadBalancerNotFoundException:
            issues.append(f"Load balancer {load_balancer_arn_or_name} not found")
            status = "not_found"
        except Exception as e:
            logger.error("Error checking ALB %s", load_balancer_arn_or_name)
            status = "error"
            issues.append(str(e))

        return {
            "resource_id": load_balancer_arn_or_name,
            "resource_type": "alb",
            "status": status,
            "last_check": datetime.datetime.utcnow().isoformat(),
            "issues": issues,
        }
