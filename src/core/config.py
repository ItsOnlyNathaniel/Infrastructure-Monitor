from re import A
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):

    #API Settings
    API_HOST: str = '0.0.0.0'
    API_PORT: str = '8000'
    LOG_LEVEL: str = 'INFO'

    #AWS Settings
    AWS_REGION: str = 'eu-west-2'
    AWS_ACCESS_KEY_ID: str = ''
    AWS_SECRET_ACCESS_KEY: str = ''

    #Database Settings
    POSTGRES_URL: str = 'POSTGRES_URL'

    #Redis Settings
    REDIS_URL: str = ''

    #Localstack Settings
    ENDPOINT_URL: str = ''

    #Monitoring Settings
    health_check_interval: int = 120 #TODO: Value should be reduced to 60 at a later stage
    remediation_timeout: int = 300
    max_retry_attempts: int = 3
    alert_threshold: int = 3

    class Config:
        env_file = ".env"
        case_sensitive=False
        extra="ignore"

settings = Settings()
