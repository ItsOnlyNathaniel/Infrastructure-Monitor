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

    #Localstack Settings

    #Monitoring Settings
    health_check_interval: int = 60
    remediation_timeout: int = 300
    max_retry_attempts: int = 3

    class Config:
        env_file = ".env"
        case_sensitive=False

settings = Settings()    