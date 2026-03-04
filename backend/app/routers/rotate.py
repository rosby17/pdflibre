from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import pypdf
from app.utils.files import tmp_path, cleanup, file_response

router = APIRouter()

@router.post("")
async def rotate_pdf(
    files: List[UploadFile] = File(...),
    angle: int = Form(90),       # 90 | -90 | 180
    target: str = Form("all"),   # all | even | odd
):
    results = []
    for upload in files:
        src = tmp_path(".pdf")
        out = tmp_path(".pdf")
        try:
            src.write_bytes(await upload.read())
            reader = pypdf.PdfReader(str(src))
            writer = pypdf.PdfWriter()

            for i, page in enumerate(reader.pages):
                page_num = i + 1
                should_rotate = (
                    target == "all" or
                    (target == "even" and page_num % 2 == 0) or
                    (target == "odd"  and page_num % 2 == 1)
                )
                if should_rotate:
                    page.rotate(angle)
                writer.add_page(page)

            with open(out, "wb") as fh:
                writer.write(fh)
            results.append((out, upload.filename))
        except Exception as e:
            cleanup(src, out)
            raise HTTPException(500, str(e))
        finally:
            cleanup(src)

    if len(results) == 1:
        out, name = results[0]
        return file_response(out, name.replace(".pdf", "_rotated.pdf"))

    import zipfile
    zip_path = tmp_path(".zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for out, name in results:
            z.write(out, name.replace(".pdf", "_rotated.pdf"))
    cleanup(*[r[0] for r in results])
    return file_response(zip_path, "rotated.zip", "application/zip")
