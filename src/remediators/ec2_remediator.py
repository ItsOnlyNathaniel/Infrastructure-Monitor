import boto3
import logging
import os

logger = logging.getLogger(__name__)

class EC2Instance:
    def __init__(self):
        self.ec2 = boto3.client(
            'ec2',
            region_name = os.getenv("AWS_DEFAULT_REGION"),
            endpoint_url = os.getenv("AWS_ENDPOINT_URL")
            )

    async def start_instance(self, instance_id: str):
        # Start a stopped instance
        logger.info("Starting instance %s", instance_id)
        self.ec2.start_instance(InstanceIds=[instance_id])

    async def reboot_instance(self, instance_id: str):
        # End a running instance
        logger.info("Ending instance %s", instance_id)
        self.ec2.reboot_instance(InstanceIds=[instance_id])

    async def reallocate_storage(self, instance_id: str):
        # Increase EBS volume size by 20%
        logger.info("Reallocating storage for instance %s", instance_id)
        volumes = self.ec2.describe_volumes(
            Filters=[
                {
                    'Name': 'attachment.instance-id',
                    'Values': [instance_id]
                }
            ]
        )['Volumes']

        for volume in volumes:
            current_size = volume['Size']
            new_size = int(current_size * 1.2)
            volume_id = volume['VolumeId']
            logger.info("Modifying volume %s from %d GiB to %d GiB", volume_id, current_size, new_size)
            self.ec2.modify_volume(
                VolumeId=volume_id,
                Size=new_size
            )

    async def remediate(self, instance_id: str, issue_type: str):
        logger.info("Remediating EC2 instance %s for error %s", instance_id, issue_type)

        #if-else statement for simple error types 
        if issue_type == "instance_stopped":
            await self.start_instance(instance_id)
        elif issue_type == "status_check_failed":
            await self.reboot_instance(instance_id)
        elif issue_type == "storage_full":
            await self.reallocate_storage(instance_id)
        else:
            raise ValueError(f"Unknown issue type: {issue_type}")
