# Imports
import boto3
import logging
import datetime
import os

logger = logging.getLogger(__name__)

class ECSMonitor:
    def __init__(self):
        #also missing endpoint_url
        self.ecs = boto3.client(
            'ecs',
            region_name = os.getenv("AWS_DEFAULT_REGION"),
            #missing endpoint_url
        )
    
    def health_check(self, service_arn: str): #Service_ARN -> Service_AmazonResourceName
        issues = []
        try:
            cluster = "default" #TODO: Parse from ARN properly
            response = self.ecs.describe_services(
                cluster = cluster,
                services = [service_arn],
            )

            if not response['services'][0]:
                issues.append(f"Service {service_arn} not found")
                status = "not_found"
            else:
                service = response['services'][0]

            #TODO: Describe tasks to check for failures

        except Exception as e:
            logger.error("Error checking ECS service %s", service_arn) 
            status = "error"
            issues.append(str(e))
        pass
