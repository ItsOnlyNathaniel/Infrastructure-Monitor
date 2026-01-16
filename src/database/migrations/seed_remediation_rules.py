"""seed remediation rules

Revision ID: seed_remediation_rules
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'seed_remediation_rules'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO remediation_rules 
        (resource_type, issue_type, description, conditions, action, auto_execute, priority, is_active, max_attempts)
        VALUES

        -- EC2 Rules
        ('EC2', 'instance_stopped', 'EC2 instance has stopped unexpectedly', 
         '{"status": "stopped", "state_reason": "User initiated"}', 'start_instance', true, 1, true, 3),

        ('EC2', 'cpu_credits_exhausted', 'EC2 burstable instance has exhausted CPU credits', 
         '{"instance_type": "t*", "cpu_credit_balance": 0}', 'switch_to_burstable', false, 2, true, 2),

        ('EC2', 'status_check_failed', 'EC2 instance status checks have failed', 
         '{"status_check_failed": true}', 'reboot_instance', true, 1, true, 3),

        ('EC2', 'storage_full', 'EC2 instance storage is full or nearly full', 
         '{"storage_usage_percent": {"gte": 90}}', 'reallocate_storage', false, 2, true, 2),


        -- ECS Rules
        ('ECS', 'failed_deployment', 'ECS service deployment has failed', 
         '{"deployment_status": "failed"}', 'rollback_deployment', false, 1, true, 2),

        ('ECS', 'instance stopped', 'ECS service instance has stopped', 
         '{"service_status": "stopped"}', 'reboot_instance', true, 1, true, 3),

        ('ECS', 'unhealthy tasks', 'ECS service has unhealthy tasks', 
         '{"unhealthy_task_count": {"gt": 0}}', 'restart_tasks', true, 2, true, 3),


        -- Lambda Rules
        ('Lambda', 'timeout', 'Lambda function execution timed out', 
         '{"error_type": "timeout"}', 'reboot_instance', true, 2, true, 3),

        ('Lambda', 'no_permisson', 'Lambda function lacks required permissions', 
         '{"error_type": "permission_denied"}', 'seek_permission', false, 1, true, 1),

        ('Lambda', 'function_error', 'Lambda function encountered an execution error', 
         '{"error_type": "function_error"}', 'invoke_function', true, 3, true, 2),


        -- RDS Rules
        ('RDS', 'instance_stopped', 'RDS instance has stopped unexpectedly', 
         '{"db_instance_status": "stopped"}', 'start_instance', true, 1, true, 3),

        ('RDS', 'status_check_failed', 'RDS instance status checks have failed', 
         '{"status_check_failed": true}', 'reboot_instance', true, 1, true, 3),

        ('RDS', 'storage_full', 'RDS instance storage is full or nearly full', 
         '{"allocated_storage_usage_percent": {"gte": 90}}', 'reallocate_storage', false, 2, true, 2),

        ('RDS', 'backup_failure', 'RDS instance backup has failed', 
         '{"backup_status": "failed"}', 'initiate_backup', false, 2, true, 2)
    """)


def downgrade():
    op.execute("""
        DELETE FROM remediation_rules 
        WHERE resource_type IN ('EC2', 'ECS', 'Lambda', 'RDS')
    """)
