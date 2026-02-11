from pydantic import Field, BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):

    #API Settings
    API_HOST = os.getenv('API_HOST')
    API_PORT = os.getenv('API_PORT')
    LOG_LEVEL = os.getenv('LOG_LEVEL')

    #AWS Settings
    AWS_REGION = os.getenv('AWS_REGION')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')

    #Database Settings
    POSTGRES_URL = os.getenv('POSTGRES_URL')

    #Redis Settings
    REDIS_URL = os.getenv('REDIS_URL')

    #Localstack Settings
    ENDPOINT_URL = os.getenv('ENDPOINT_URL')

    #Monitoring Settings
    health_check_interval: int = 120 #TODO: Value should be reduced to 60 at a later stage
    remediation_timeout: int = 300
    max_retry_attempts: int = 3
    alert_threshold: int = 3

    class Config:
        env_file = ".env"
        case_sensitive=False

settings = Settings()
