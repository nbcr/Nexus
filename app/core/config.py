import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Generate an absolute path to the .env file to avoid path issues [citation:5]
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    
    # Database
    database_url: str
    database_url_sync: str
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"

    # Use the new configuration style for Pydantic V2 [citation:6]
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        case_sensitive=False  # If you want environment variables to be case-insensitive
    )

settings = Settings()
