"""Application configuration via Pydantic BaseSettings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./finalat.db",
        description="Database connection URL. PostgreSQL for production, SQLite for local dev.",
    )

    # Encryption
    FERNET_KEY: str = Field(
        default="",
        description="Fernet encryption key for field-level encryption. Required in production.",
    )

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed CORS origins.",
    )

    # Firebase
    FIREBASE_PROJECT_ID: str = Field(
        default="",
        description="Firebase project ID for JWT verification.",
    )
    FIREBASE_WEB_API_KEY: str = Field(
        default="",
        description="Firebase Web API key.",
    )

    # Banxico API
    BMX_TOKEN: str = Field(
        default="",
        description="Banco de México SIE API token for CETES rates.",
    )

    # AWS / Bedrock
    AWS_REGION: str = Field(
        default="us-east-1",
        description="AWS region for Bedrock and other services.",
    )
    AWS_ACCESS_KEY_ID: str = Field(
        default="",
        description="AWS access key ID.",
    )
    AWS_SECRET_ACCESS_KEY: str = Field(
        default="",
        description="AWS secret access key.",
    )
    BEDROCK_MODEL_ID: str = Field(
        default="amazon.nova-pro-v1:0",
        description="Amazon Bedrock model identifier.",
    )

    # Application
    APP_ENV: str = Field(
        default="development",
        description="Application environment: development, staging, production.",
    )
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode.",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite (local dev fallback)."""
        return self.DATABASE_URL.startswith("sqlite")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
