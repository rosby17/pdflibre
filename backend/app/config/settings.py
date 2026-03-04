from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Union
import json
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "PDFLibre"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS — Railway env var should be a plain string or comma-separated list
    # e.g.  ALLOWED_ORIGINS=*
    # e.g.  ALLOWED_ORIGINS=https://pdflibre.vercel.app,https://pdflibre.com
    ALLOWED_ORIGINS: str = "*"

    # File limits
    MAX_FILE_SIZE_MB: int = 100
    MAX_FILES_PER_REQUEST: int = 20
    TMP_DIR: str = "/tmp/pdflibre"
    FILE_TTL_SECONDS: int = 3600

    # Rate limiting (requests per minute per IP)
    RATE_LIMIT_RPM: int = 30

    # Job queue
    MAX_CONCURRENT_JOBS: int = 4

    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS as comma-separated string or JSON array."""
        val = self.ALLOWED_ORIGINS.strip()
        if val == "*":
            return ["*"]
        # Try JSON array first: ["https://a.com","https://b.com"]
        if val.startswith("["):
            try:
                return json.loads(val)
            except Exception:
                pass
        # Comma-separated: https://a.com,https://b.com
        return [v.strip() for v in val.split(",") if v.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
