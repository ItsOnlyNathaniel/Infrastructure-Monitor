# Imports
import boto3
import logging
#import datetime
import os

logger = logging.getLogger(__name__)

class ECSMonitor:
    def __init__(self):
        self.ecs = boto3.client(
            'ecs',
            region_name = os.getenv("AWS_DEFAULT_REGION"),
            #missing endpoint_url
        )
    
    def health_check(self, instance_id: str):
        pass
