import boto3
import logging
import os
from dotenv import load_dotenv


logger = logging.getLogger(__name__)
load_dotenv()

class EC2Instance:
    def __init__(self):
        self.ec2 = boto3.client(
            'ec2',
            region_name = os.getenv("AWS_DEFAULT_REGION"),
            #missing endpoint_url
            )

    async def _start_instance(self, instance_id: str):
        # Start a stopped instance
        logger.info(f"Starting instance {instance_id}")
        self.ec2.start_instance(InstanceIds=[instance_id])

    async def reboot_instance(self, instance_id: str):
        # End a running instance
        logger.info(f"Ending instance {instance_id}")
        self.ex2.reboot_instance(InstanceIds=[instance_id])

    async def remediate(self, instance_id: str, issue_type: str):
        logger.info(f"Remediating EC2 instance {instance_id} for error {issue_type}")

        #if-else statement for simple error types 
        if issue_type == "instance_stopped":
            await self._start_instance(instance_id)
        elif issue_type == "status_check_failed":
            await self._reboot_instance(instance_id)
        else:
            raise ValueError(f"Unknown issue type: {issue_type}")
