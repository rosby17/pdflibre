import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware import RateLimitMiddleware, FileSizeMiddleware
from app.jobs import queue
from app.routers import merge, split, compress, rotate, pdf2jpg, jpg2pdf, watermark, protect, jobs

settings = get_settings()


async def _cleanup_loop():
    while True:
        await asyncio.sleep(600)
        queue.cleanup_old_jobs()
        tmp = Path(settings.TMP_DIR)
        if tmp.exists():
            import time
            cutoff = time.time() - settings.FILE_TTL_SECONDS
            for f in tmp.iterdir():
                try:
                    if f.stat().st_mtime < cutoff:
                        if f.is_dir():
                            import shutil; shutil.rmtree(f, ignore_errors=True)
                        else:
                            f.unlink()
                except Exception:
                    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.TMP_DIR).mkdir(parents=True, exist_ok=True)
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",   # always on — toggle access via DEBUG env var if needed
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(FileSizeMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(merge.router,    prefix="/api/merge",    tags=["PDF"])
app.include_router(split.router,    prefix="/api/split",    tags=["PDF"])
app.include_router(compress.router, prefix="/api/compress", tags=["PDF"])
app.include_router(rotate.router,   prefix="/api/rotate",   tags=["PDF"])
app.include_router(pdf2jpg.router,  prefix="/api/pdf2jpg",  tags=["Convert"])
app.include_router(jpg2pdf.router,  prefix="/api/jpg2pdf",  tags=["Convert"])
app.include_router(watermark.router,prefix="/api/watermark",tags=["PDF"])
app.include_router(protect.router,  prefix="/api/protect",  tags=["Security"])
app.include_router(jobs.router,     prefix="/api/jobs",     tags=["Jobs"])


@app.get("/health", tags=["System"])
def health():
    return {
        "status":  "ok",
        "version": settings.VERSION,
        "max_file_mb": settings.MAX_FILE_SIZE_MB,
        "rate_limit_rpm": settings.RATE_LIMIT_RPM,
    }
