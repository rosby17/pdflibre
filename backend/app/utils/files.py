import os
import uuid
import shutil
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi import HTTPException

TMPDIR = Path("/tmp/pdflibre")

def tmp_path(suffix: str = ".pdf") -> Path:
    """Generate a unique temp file path."""
    TMPDIR.mkdir(parents=True, exist_ok=True)
    return TMPDIR / f"{uuid.uuid4().hex}{suffix}"

def cleanup(*paths):
    """Delete temp files/dirs silently."""
    for p in paths:
        try:
            if Path(p).is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                os.unlink(p)
        except Exception:
            pass

def file_response(path: Path, filename: str, media_type: str = "application/pdf") -> FileResponse:
    if not path.exists():
        raise HTTPException(500, "Fichier de sortie introuvable")
    return FileResponse(
        path=str(path),
        filename=filename,
        media_type=media_type,
        background=None,
    )
