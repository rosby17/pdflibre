from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import pypdf, zipfile, shutil
from pathlib import Path
from app.utils.files import tmp_path, cleanup, file_response

router = APIRouter()

def parse_ranges(spec: str, total: int) -> list[int]:
    """Parse '1-3,5,7-9' into 0-indexed page list."""
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a)-1, int(b)))
        else:
            pages.add(int(part)-1)
    return sorted(p for p in pages if 0 <= p < total)

@router.post("")
async def split_pdf(
    file: UploadFile = File(...),
    mode: str = Form("all"),        # all | range | specific
    pages: Optional[str] = Form(None),
):
    src = tmp_path(".pdf")
    workdir = tmp_path("")   # used as dir
    workdir.mkdir(parents=True, exist_ok=True)
    out_zip = tmp_path(".zip")

    try:
        src.write_bytes(await file.read())
        reader = pypdf.PdfReader(str(src))
        total = len(reader.pages)

        if mode == "all":
            indices = list(range(total))
            # One file per page
            out_files = []
            for i in indices:
                w = pypdf.PdfWriter()
                w.add_page(reader.pages[i])
                p = workdir / f"page_{i+1:03d}.pdf"
                with open(p, "wb") as fh:
                    w.write(fh)
                out_files.append(p)
        else:
            if not pages:
                raise HTTPException(400, "Spécifiez les pages")
            indices = parse_ranges(pages, total)
            if not indices:
                raise HTTPException(400, "Aucune page valide")
            out_files = []
            for i in indices:
                w = pypdf.PdfWriter()
                w.add_page(reader.pages[i])
                p = workdir / f"page_{i+1:03d}.pdf"
                with open(p, "wb") as fh:
                    w.write(fh)
                out_files.append(p)

        # Zip all output files
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for f in out_files:
                z.write(f, f.name)

        return file_response(out_zip, "split_pages.zip", "application/zip")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cleanup(src, workdir)
