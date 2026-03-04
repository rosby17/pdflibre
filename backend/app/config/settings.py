from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "PDFLibre"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS — set to your Vercel URL in production
    # e.g. ALLOWED_ORIGINS=https://pdflibre.vercel.app
    ALLOWED_ORIGINS: List[str] = ["*"]

    # File limits
    MAX_FILE_SIZE_MB: int = 100          # per file
    MAX_FILES_PER_REQUEST: int = 20
    TMP_DIR: str = "/tmp/pdflibre"
    FILE_TTL_SECONDS: int = 3600         # auto-delete after 1h

    # Rate limiting (requests per minute per IP)
    RATE_LIMIT_RPM: int = 30

    # Job queue
    MAX_CONCURRENT_JOBS: int = 4         # tune to Railway instance size

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
