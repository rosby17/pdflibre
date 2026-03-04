from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import zipfile
from pdf2image import convert_from_bytes
from app.utils.files import tmp_path, cleanup, file_response

router = APIRouter()

FMT_MAP = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP"}

@router.post("")
async def pdf_to_jpg(
    files: List[UploadFile] = File(...),
    dpi: int  = Form(150),
    fmt: str  = Form("jpg"),   # jpg | png | webp
):
    pil_fmt = FMT_MAP.get(fmt.lower(), "JPEG")
    ext = fmt.lower()
    if ext == "jpg": ext = "jpg"

    zip_path = tmp_path(".zip")
    srcs = []

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for upload in files:
                data = await upload.read()
                srcs.append(upload.filename)
                images = convert_from_bytes(data, dpi=dpi, fmt=pil_fmt)
                base = upload.filename.replace(".pdf", "")
                for i, img in enumerate(images):
                    img_path = tmp_path(f".{ext}")
                    img.save(str(img_path), format=pil_fmt)
                    z.write(img_path, f"{base}_page{i+1:03d}.{ext}")
                    cleanup(img_path)

        return file_response(zip_path, "images.zip", "application/zip")

    except Exception as e:
        cleanup(zip_path)
        raise HTTPException(500, str(e))
