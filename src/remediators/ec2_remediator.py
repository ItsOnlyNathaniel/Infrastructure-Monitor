import boto3
import logging
import os


logger = logging.getLogger(__name__)

class EC2Instance:
    def __init__(self):
        self.ec2 = boto3.client(
            'ec2',
            region_name = os.getenv("AWS_DEFAULT_REGION"),
            #missing endpoint_url
            )

    async def start_instance(self, instance_id: str):
        # Start a stopped instance
        logger.info("Starting instance %s", instance_id)
        self.ec2.start_instance(InstanceIds=[instance_id])

    async def reboot_instance(self, instance_id: str):
        # End a running instance
        logger.info("Ending instance %s", instance_id)
        self.ec2.reboot_instance(InstanceIds=[instance_id])

    async def remediate(self, instance_id: str, issue_type: str):
        logger.info("Remediating EC2 instance %s for error %s", instance_id, issue_type)

        #if-else statement for simple error types 
        if issue_type == "instance_stopped":
            await self.start_instance(instance_id)
        elif issue_type == "status_check_failed":
            await self.reboot_instance(instance_id)
        else:
            raise ValueError(f"Unknown issue type: {issue_type}")
