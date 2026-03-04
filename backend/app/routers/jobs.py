from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from app.jobs import queue, JobStatus

router = APIRouter()


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    job = queue.get(job_id)
    if not job:
        raise HTTPException(404, "Job introuvable ou expiré")

    return {
        "job_id":   job.job_id,
        "status":   job.status,
        "error":    job.error,
        "filename": job.filename if job.status == JobStatus.DONE else None,
    }


@router.get("/{job_id}/download")
async def download_job_result(job_id: str):
    job = queue.get(job_id)
    if not job:
        raise HTTPException(404, "Job introuvable ou expiré")
    if job.status == JobStatus.PENDING or job.status == JobStatus.RUNNING:
        raise HTTPException(202, "Job en cours de traitement")
    if job.status == JobStatus.ERROR:
        raise HTTPException(500, job.error or "Erreur de traitement")

    result = Path(job.result)
    if not result.exists():
        raise HTTPException(410, "Fichier expiré — veuillez relancer le traitement")

    return FileResponse(
        path=str(result),
        filename=job.filename,
        media_type=job.mime,
    )
