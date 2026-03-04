from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings

settings = get_settings()

class FileSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path.startswith("/api/"):
            content_length = request.headers.get("content-length")
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                max_mb = settings.MAX_FILE_SIZE_MB * settings.MAX_FILES_PER_REQUEST
                if size_mb > max_mb:
                    raise HTTPException(
                        413,
                        f"Payload trop large. Maximum : {max_mb} MB"
                    )
        return await call_next(request)
