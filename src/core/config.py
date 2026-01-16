from pydantic import Field, BaseSettings

class Settings(BaseSettings):
    #API Settings
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    #Database Settings
    postgres_url: str = Field(alias="POSTGRES_URL")

    #Redis Settings
    redis_url: str = Field(alias="REDIS_URL")

    #AWS Settings
    aws_region: str = Field(default="us-east-1", alias="AWS_DEFAULT_REGION")
    aws_access_key_id: str = Field(default="test", alias="AWS_ACCESS_KEY_ID")

    #Localstack Settings
    endpoint_url = Field(default=None, alias="AWS_ENDPOINT_URL")

    #Monitoring Settings
    health_check_interval: int = 120 #TODO: Value should be reduced to 60 at a later stage
    remediation_timeout: int = 300
    max_retry_attempts: int = 3
    alert_threshold: int = 3

    class Config:
        env_file = ".env"
        case_sensitive=False

settings = Settings()
