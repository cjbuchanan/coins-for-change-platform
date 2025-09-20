"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/coins_for_change",
        description="Database connection URL"
    )
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow connections")
    database_pool_timeout: int = Field(default=30, description="Database pool timeout in seconds")
    
    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_max_connections: int = Field(default=100, description="Redis max connections")
    redis_socket_timeout: int = Field(default=5, description="Redis socket timeout in seconds")
    
    # OpenSearch settings
    opensearch_url: str = Field(
        default="http://localhost:9200",
        description="OpenSearch connection URL"
    )
    opensearch_username: Optional[str] = Field(default=None, description="OpenSearch username")
    opensearch_password: Optional[str] = Field(default=None, description="OpenSearch password")
    opensearch_timeout: int = Field(default=30, description="OpenSearch timeout in seconds")
    opensearch_max_retries: int = Field(default=3, description="OpenSearch max retries")
    
    # Security settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_seconds: int = Field(default=3600, description="JWT expiration in seconds")
    password_min_length: int = Field(default=8, description="Minimum password length")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins"
    )
    
    # External services
    smtp_host: Optional[str] = Field(default=None, description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="SMTP use TLS")
    
    # Observability settings
    otel_exporter_jaeger_endpoint: Optional[str] = Field(
        default=None,
        description="Jaeger exporter endpoint"
    )
    prometheus_gateway_url: Optional[str] = Field(
        default=None,
        description="Prometheus pushgateway URL"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DevelopmentSettings(Settings):
    """Development environment settings."""
    debug: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings."""
    debug: bool = False
    log_level: str = "INFO"


class TestingSettings(Settings):
    """Testing environment settings."""
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "postgresql+asyncpg://test:test@localhost:5432/coins_for_change_test"


@lru_cache()
def get_settings() -> Settings:
    """Get application settings based on environment."""
    import os
    
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()