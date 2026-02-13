import boto3
import logging
from src.core.config import Settings
import os

logger = logging.getLogger(__name__)

class LambdaInstance:
    def __init__(self):
        self.lambda_client = boto3.client(
            'lambda',
            region_name = Settings.AWS_REGION,
            endpoint_url = Settings.ENDPOINT_URL
            )

    async def reboot_instance(self, function_name: str):
        # Update function configuration to trigger a restart
        logger.info("Rebooting Lambda function %s", function_name)
        self.lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': {
                    'RESTART_TRIGGER': str(os.urandom(8))
                }
            }
        )

    async def seek_permission(self, function_name: str):
        # Placeholder for seeking permission logic
        logger.info("Seeking permission for Lambda function %s", function_name)
        #TODO: Implement permission seeking logic here

    async def invoke_function(self, function_name: str):
        # Invoke a Lambda function
        logger.info("Invoking Lambda function %s", function_name)
        self.lambda_client.invoke(FunctionName=function_name, InvocationType='Event')

    async def remediate(self, resource_id: str, issue_type: str):
        logger.info("Remediating Lambda resource %s for error %s", resource_id, issue_type)

        if issue_type == "timeout":
            await self.reboot_instance(resource_id)
        elif issue_type == "no_permisson":
            await self.seek_permission(resource_id)
        elif issue_type == "function_error":
            await self.invoke_function(resource_id)
        else:
            raise ValueError(f"Unknown issue type: {issue_type}")
