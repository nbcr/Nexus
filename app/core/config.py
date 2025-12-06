import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Generate an absolute path to the .env file to avoid path issues [citation:5]
DOTENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Nexus"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    environment: str = "development"
    debug: bool = True

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Frontend
    FRONTEND_URL: str = "http://localhost:8000"

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/nexus"
    database_url_sync: str = "postgresql://localhost:5432/nexus"

    # Redis (for Celery if needed)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://comdat.ca",
        "https://api.test.comdat.ca",
    ]

    # Email Configuration
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SENDER_EMAIL: str = "nexus@comdat.ca"
    ADMIN_EMAIL: str = "webmaster@comdat.ca"
    BREVO_API_KEY: str = ""
    BREVO_WEBHOOK_TOKEN: str = ""

    # Use the new configuration style for Pydantic V2
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        case_sensitive=False,  # If you want environment variables to be case-insensitive
        extra="ignore",  # Ignore extra fields from .env file
    )


settings = Settings()
