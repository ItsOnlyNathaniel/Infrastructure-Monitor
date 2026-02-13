# Imports
import boto3
from botocore.exceptions import ClientError
import logging
import datetime
import asyncio
from typing import Dict, List, Any
from src.core.config import Settings

logger = logging.getLogger(__name__)


class CloudwatchMonitor:
    def __init__(self):
        self.cloudwatch_client = boto3.client(
            "cloudwatch",
            region_name=Settings.AWS_REGION,
            endpoint_url=Settings.ENDPOINT_URL
        )

    async def _get_metric_data(
        self,
        namespace: str,
        metric_name: str,
        dimensions: List[Dict[str, str]],
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        period: int,
        statistics: List[str],
    ) -> Dict[str, Any]:
        """Helper method to get metric data from CloudWatch."""
        try:
            response = await asyncio.to_thread(
                self.cloudwatch_client.get_metric_statistics,
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=statistics,
            )
            return {
                "metric_name": metric_name,
                "statistics": statistics,
                "datapoints": response.get("Datapoints", []),
            }
        except ClientError as e:
            error_msg = f"Error fetching {metric_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "metric_name": metric_name,
                "statistics": statistics,
                "datapoints": [],
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Unexpected error fetching {metric_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "metric_name": metric_name,
                "statistics": statistics,
                "datapoints": [],
                "error": error_msg,
            }

    async def get_ec2_metrics(
        self,
        instance_id: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        period: int = 300,
    ) -> Dict[str, Any]:

        namespace = "AWS/EC2"
        dimensions = [{"Name": "InstanceId", "Value": instance_id}]
        statistics = ["Average", "Maximum", "Minimum"]

        metrics_to_collect = [
            "CPUUtilization",
            "NetworkIn",
            "NetworkOut",
            "DiskReadOps",
            "DiskWriteOps",
        ]

        metrics = {}
        errors = []

        tasks = [
            self._get_metric_data(
                namespace, metric, dimensions, start_time, end_time, period, statistics
            )
            for metric in metrics_to_collect
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            metric_name = result["metric_name"]
            if "error" in result:
                errors.append(result["error"])
            metrics[metric_name] = {
                "statistics": result["statistics"],
                "datapoints": result["datapoints"],
            }

        return {
            "resource_id": instance_id,
            "resource_type": "ec2",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "metrics": metrics,
            "errors": errors,
        }

    async def get_ecs_metrics(
        self,
        cluster_name: str,
        service_name: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        period: int = 300,
    ) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for an ECS service.

        Args:
            cluster_name: The ECS cluster name
            service_name: The ECS service name
            start_time: Start time for metric collection
            end_time: End time for metric collection
            period: Period in seconds (default: 300)

        Returns:
            Dictionary containing metrics data
        """
        namespace = "AWS/ECS"
        dimensions = [
            {"Name": "ClusterName", "Value": cluster_name},
            {"Name": "ServiceName", "Value": service_name},
        ]
        statistics = ["Average", "Maximum", "Minimum"]

        metrics_to_collect = [
            "CPUUtilization",
            "MemoryUtilization",
            "RunningTaskCount",
            "DesiredTaskCount",
        ]

        metrics = {}
        errors = []

        tasks = [
            self._get_metric_data(
                namespace, metric, dimensions, start_time, end_time, period, statistics
            )
            for metric in metrics_to_collect
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            metric_name = result["metric_name"]
            if "error" in result:
                errors.append(result["error"])
            metrics[metric_name] = {
                "statistics": result["statistics"],
                "datapoints": result["datapoints"],
            }

        resource_id = f"{cluster_name}/{service_name}"
        return {
            "resource_id": resource_id,
            "resource_type": "ecs",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "metrics": metrics,
            "errors": errors,
        }

    async def get_lambda_metrics(
        self,
        function_name: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        period: int = 300,
    ) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for a Lambda function.

        Args:
            function_name: The Lambda function name
            start_time: Start time for metric collection
            end_time: End time for metric collection
            period: Period in seconds (default: 300)

        Returns:
            Dictionary containing metrics data
        """
        namespace = "AWS/Lambda"
        dimensions = [{"Name": "FunctionName", "Value": function_name}]

        # Metrics with Sum statistics
        sum_metrics = ["Invocations", "Errors", "Throttles"]
        # Metrics with Average statistics
        avg_metrics = ["Duration", "ConcurrentExecutions"]

        metrics = {}
        errors = []

        # Collect Sum metrics
        sum_tasks = [
            self._get_metric_data(
                namespace,
                metric,
                dimensions,
                start_time,
                end_time,
                period,
                ["Sum"],
            )
            for metric in sum_metrics
        ]

        # Collect Average metrics
        avg_tasks = [
            self._get_metric_data(
                namespace,
                metric,
                dimensions,
                start_time,
                end_time,
                period,
                ["Average"],
            )
            for metric in avg_metrics
        ]

        all_tasks = sum_tasks + avg_tasks
        results = await asyncio.gather(*all_tasks)

        for result in results:
            metric_name = result["metric_name"]
            if "error" in result:
                errors.append(result["error"])
            metrics[metric_name] = {
                "statistics": result["statistics"],
                "datapoints": result["datapoints"],
            }

        return {
            "resource_id": function_name,
            "resource_type": "lambda",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "metrics": metrics,
            "errors": errors,
        }

    async def get_rds_metrics(
        self,
        db_instance_identifier: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        period: int = 300,
    ) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for an RDS instance.

        Args:
            db_instance_identifier: The RDS instance identifier
            start_time: Start time for metric collection
            end_time: End time for metric collection
            period: Period in seconds (default: 300)

        Returns:
            Dictionary containing metrics data
        """
        namespace = "AWS/RDS"
        dimensions = [{"Name": "DBInstanceIdentifier", "Value": db_instance_identifier}]
        statistics = ["Average", "Maximum", "Minimum"]

        metrics_to_collect = [
            "CPUUtilization",
            "DatabaseConnections",
            "FreeableMemory",
            "FreeStorageSpace",
            "ReadLatency",
            "WriteLatency",
        ]

        metrics = {}
        errors = []

        tasks = [
            self._get_metric_data(
                namespace, metric, dimensions, start_time, end_time, period, statistics
            )
            for metric in metrics_to_collect
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            metric_name = result["metric_name"]
            if "error" in result:
                errors.append(result["error"])
            metrics[metric_name] = {
                "statistics": result["statistics"],
                "datapoints": result["datapoints"],
            }

        return {
            "resource_id": db_instance_identifier,
            "resource_type": "rds",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "metrics": metrics,
            "errors": errors,
        }
