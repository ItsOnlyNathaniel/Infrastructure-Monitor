# Imports
import boto3
import logging
#import datetime
import os

logger = logging.getLogger(__name__)

class EC2Monitor:
    def __init__(self):
        self.ec2 = boto3.client(
            'ec2',
            region_name = os.getenv("AWS_DEFAULT_REGION"),
            #missing endpoint_url
        )
    
    def health_check(self, instance_id: str):
        pass
