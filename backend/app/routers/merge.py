from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import pypdf
from app.utils.files import tmp_path, cleanup, file_response

router = APIRouter()

@router.post("")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(400, "Au moins 2 fichiers PDF requis")

    saved = []
    try:
        writer = pypdf.PdfWriter()

        for f in files:
            p = tmp_path(".pdf")
            p.write_bytes(await f.read())
            saved.append(p)
            reader = pypdf.PdfReader(str(p))
            for page in reader.pages:
                writer.add_page(page)

        out = tmp_path(".pdf")
        saved.append(out)
        with open(out, "wb") as fh:
            writer.write(fh)

        return file_response(out, "merged.pdf")

    except Exception as e:
        cleanup(*saved)
        raise HTTPException(500, str(e))
