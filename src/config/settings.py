"""Application settings and configuration."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.

    Attributes:
        environment: Environment name (development, staging, production)
        log_level: Logging level
        log_file: Path to log file

        postgres_host: PostgreSQL host
        postgres_port: PostgreSQL port
        postgres_db: Database name
        postgres_user: Database user
        postgres_password: Database password

        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password

        redis_host: Redis host
        redis_port: Redis port

        model_cache_dir: Directory for cached models
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/app.log"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "code_review"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Models
    model_cache_dir: str = "models/checkpoints"

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL.

        Returns:
            PostgreSQL connection string
        """
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL.

        Returns:
            Redis connection string
        """
        return f"redis://{self.redis_host}:{self.redis_port}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()
