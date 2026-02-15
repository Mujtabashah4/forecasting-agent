"""
Configuration settings for Forecasting Agent API
Follows security requirements from implementation guide
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with security requirements"""

    # API Configuration
    API_SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    API_TITLE: str = "Forecasting Agent API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # LLM Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT: int = 60

    # Authentication & Security
    SECRET_KEY: str = Field(..., description="Secret key for authentication")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    TOKEN_EXPIRE_MINUTES: int = 60

    # IP Security (comma-separated list)
    # Default includes localhost for both IPv4 and IPv6
    ALLOWED_IPS: str = "127.0.0.1,::1,localhost"
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/forecasting-agent.log"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # API Versioning
    API_V1_PREFIX: str = "/api/v1"

    @property
    def allowed_ips_list(self) -> List[str]:
        """Parse allowed IPs from comma-separated string"""
        return [ip.strip() for ip in self.ALLOWED_IPS.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
