import boto3
import logging
import os
import re

logger = logging.getLogger(__name__)

class ECSInstance:
    def __init__(self):
        self.ecs = boto3.client(
            'ecs',
            region_name = os.getenv("AWS_DEFAULT_REGION"),
            #missing endpoint_url
            )
    
    def _parse_resource_id(self, resource_id: str): #Generated
        """
        Parse resource_id to extract cluster and service name.
        Supports both ARN format and cluster/service format.
        
        ARN format: arn:aws:ecs:region:account:service/cluster-name/service-name
        Simple format: cluster-name/service-name or just service-name (default cluster)
        """
        # Try ARN format first
        arn_pattern = r'arn:aws:ecs:[^:]+:[^:]+:service/([^/]+)/(.+)'
        match = re.match(arn_pattern, resource_id)
        if match:
            cluster = match.group(1)
            service = match.group(2)
            return cluster, service
        
        # Try cluster/service format
        if '/' in resource_id:
            parts = resource_id.split('/', 1)
            return parts[0], parts[1]
        
        # If no cluster specified, use 'default' cluster
        return 'default', resource_id

    async def _start_instance(self, instance_id: str):
        # Start a stopped instance
        logger.info("Starting instance %s", instance_id)
        self.ecs.start_instance(InstanceIds=[instance_id])

    async def reboot_instance(self, cluster: str, service: str):
        # Force a new deployment to restart the service
        logger.info("Rebooting service %s in cluster %s by forcing new deployment", service, cluster)
        self.ecs.update_service(
            cluster=cluster,
            service=service,
            forceNewDeployment=True
        )

    async def restart_tasks(self, cluster: str, service: str):
        # Force restart of unhealthy tasks
        logger.info("Restarting tasks for service %s", service)
        tasks_response = self.ecs.list_tasks(
            cluster=cluster,
            serviceName=service
        )
        # Stop tasks (ECS will restart them automatically)
        for task_arn in tasks_response.get('taskArns', []):
            logger.info("Stopping task %s", task_arn)
            self.ecs.stop_task(cluster=cluster, task=task_arn)

    async def rollback_deployment(self, cluster: str, service: str): #Generated
        """
        Rollback ECS service to previous task definition revision.
        
        Args:
            cluster: ECS cluster name
            service: ECS service name
        """
        logger.info("Rolling back deployment for service %s in cluster %s", service, cluster)
        
        try:
            # Get current service configuration
            service_response = self.ecs.describe_services(
                cluster=cluster,
                services=[service]
            )
            
            if not service_response.get('services'):
                raise ValueError(f"Service {service} not found in cluster {cluster}")
            
            current_service = service_response['services'][0]
            current_task_def = current_service.get('taskDefinition')
            
            if not current_task_def:
                raise ValueError(f"No task definition found for service {service}")
            
            logger.info("Current task definition: %s", current_task_def)
            
            # Extract task definition family and revision
            # Format: family:revision (e.g., "my-task-def:5")
            task_def_parts = current_task_def.split(':')
            if len(task_def_parts) != 2:
                raise ValueError(f"Invalid task definition format: {current_task_def}")
            
            task_family = task_def_parts[0]
            current_revision = int(task_def_parts[1])
            
            logger.info("Task family: %s, Current revision: %s", task_family, current_revision)
            
            # Check if there's a previous revision
            if current_revision <= 1:
                raise ValueError("No previous revision available. Current revision is {current_revision}")
            
            # Get previous revision
            previous_revision = current_revision - 1
            previous_task_def = f"{task_family}:{previous_revision}"
            
            # Verify previous task definition exists
            try:
                self.ecs.describe_task_definition(taskDefinition=previous_task_def)
                logger.info("Previous task definition found: %s", previous_task_def)
            except self.ecs.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'ClientException':
                    raise ValueError("Previous task definition %s not found: ", previous_task_def)
                raise
            
            # Update service to use previous task definition
            logger.info("Updating service to use task definition: %s", previous_task_def)
            update_response = self.ecs.update_service(
                cluster=cluster,
                service=service,
                taskDefinition=previous_task_def,
                forceNewDeployment=True
            )
            
            logger.info("Service update initiated. Deployment ID: %s", update_response['service']['deployments'][0]['id'])
            logger.info("Successfully rolled back service %s to task definition %s", service, previous_task_def)
            
            return {
                "status": "success",
                "previous_task_definition": previous_task_def,
                "current_task_definition": current_task_def,
                "deployment_id": update_response['service']['deployments'][0]['id']
            }
            
        except ValueError as e:
            logger.error("Rollback failed: %s", str(e))
            raise
        except self.ecs.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error("AWS API error during rollback: %s - %s", error_code, error_message)
            raise Exception("Rollback failed: %s - %s", error_code, error_message)
        except Exception as e:
            logger.error("Unexpected error during rollback: %s", str(e))
            raise

    async def remediate(self, resource_id: str, issue_type: str):
        """
        Remediate ECS service based on issue type.
        
        Args:
            resource_id: ECS service identifier (ARN or cluster/service format)
            issue_type: Type of issue to remediate
        """
        logger.info("Remediating ECS resource %s for error %s", resource_id, issue_type)
        
        # Parse resource_id to extract cluster and service
        cluster, service = self._parse_resource_id(resource_id)
        logger.info("Parsed cluster: %s, service: %s", cluster, service)

        if issue_type == "failed_deployment":
            await self.rollback_deployment(cluster, service)
        elif issue_type == "instance stopped":
            await self.reboot_instance(cluster, service)
        elif issue_type == "unhealthy tasks":
            await self.restart_tasks(cluster, service)
