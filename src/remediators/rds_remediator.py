from datetime import datetime
import boto3
import logging
from src.core.config import Settings

logger = logging.getLogger(__name__)

class RDSInstance:
    def __init__(self):
        self.rds = boto3.client(
            'rds',
            region_name = Settings.AWS_REGION,
            endpoint_url = Settings.ENDPOINT_URL
            )

    async def start_instance(self, db_instance_identifier: str):
        # Start a stopped RDS instance
        logger.info("Starting RDS instance %s", db_instance_identifier)
        self.rds.start_db_instance(DBInstanceIdentifier=db_instance_identifier)

    async def reboot_instance(self, db_instance_identifier: str):
        # Reboot an RDS instance
        logger.info("Rebooting RDS instance %s", db_instance_identifier)
        self.rds.reboot_db_instance(DBInstanceIdentifier=db_instance_identifier)

    async def reallocate_storage(self, db_instance_identifier: str):
        # Increase allocated storage by 20%
        logger.info("Reallocating storage for RDS instance %s", db_instance_identifier)
        response = self.rds.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        current_storage = response['DBInstances'][0]['AllocatedStorage']
        new_storage = int(current_storage * 1.2)
        self.rds.modify_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            AllocatedStorage=new_storage,
            ApplyImmediately=True
        )

    async def initiate_backup(self, db_instance_identifier: str):
        # Initiate a manual snapshot backup
        logger.info("Initiating backup for RDS instance %s", db_instance_identifier)
        snapshot_identifier = f"{db_instance_identifier}-manual-snapshot-{int(datetime.datetime.now().timestamp())}"
        self.rds.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_identifier,
            DBInstanceIdentifier=db_instance_identifier
        )

    async def remediate(self, resource_id: str, issue_type: str):
        logger.info("Remediating RDS resource %s for error %s", resource_id, issue_type)

        if issue_type == "instance_stopped":
            await self.start_instance(resource_id)
        elif issue_type == "status_check_failed":
            await self.reboot_instance(resource_id)
        elif issue_type == "storage_full":
            await self.reallocate_storage(resource_id)
        elif issue_type == "backup_failure":
            await self.initiate_backup(resource_id)
        else:
            raise ValueError(f"Unknown issue type: {issue_type}")
