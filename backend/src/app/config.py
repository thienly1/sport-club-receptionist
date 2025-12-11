"""
Application Configuration
Handles all environment variables and settings
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Sport Club AI Receptionist"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = ""

    # Database (Supabase)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    DATABASE_URL: str = ""

    # JWT & Authentication
    JWT_SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # VAPI Configuration
    VAPI_API_KEY: str = ""
    VAPI_ASSISTANT_ID: str = ""
    VAPI_PHONE_NUMBER: str = ""
    VAPI_BASE_URL: str = ""

    # VAPI SIP Configuration
    FREE_VAPI_SIP_USERNAME: str = ""
    FREE_VAPI_SIP_PASSWORD: str = ""
    FREE_VAPI_SIP: str = ""
    VAPI_SIP_DOMAIN: str = "sip.vapi.ai"

    # Twilio (SMS Notifications - Optional)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # SMS Provider Choice
    SMS_PROVIDER: str = "twilio"

    # Matchi Integration
    MATCHI_BASE_URL: str = "https://matchi.se"
    MATCHI_API_KEY: str = ""

    # Manager Contact
    MANAGER_PHONE_NUMBER: str = ""

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = BASE_DIR / "src" / ".env"  # or BASE_DIR / "src" / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
