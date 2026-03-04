from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import pypdf
from app.utils.files import tmp_path, cleanup, file_response

router = APIRouter()

# quality map: 0=high-quality/low-compression, 2=low-quality/high-compression
QUALITY_MAP = {
    "0": 95,   # faible compression
    "1": 72,   # moyen
    "2": 45,   # élevé
}

@router.post("")
async def compress_pdf(
    files: List[UploadFile] = File(...),
    level: str = Form("1"),
):
    quality = QUALITY_MAP.get(level, 72)
    results = []

    for upload in files:
        src = tmp_path(".pdf")
        out = tmp_path(".pdf")
        try:
            src.write_bytes(await upload.read())
            reader = pypdf.PdfReader(str(src))
            writer = pypdf.PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # Compress embedded images
            for page in writer.pages:
                for img in page.images:
                    try:
                        img.replace(img.image, quality=quality)
                    except Exception:
                        pass  # skip uncompressable images

            writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)

            with open(out, "wb") as fh:
                writer.write(fh)

            results.append(out)
        except Exception as e:
            cleanup(src, out)
            raise HTTPException(500, f"Erreur sur {upload.filename}: {e}")
        finally:
            cleanup(src)

    if len(results) == 1:
        name = upload.filename.replace(".pdf", "_compressed.pdf")
        return file_response(results[0], name)

    # Multiple files → zip
    import zipfile
    zip_path = tmp_path(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for i, r in enumerate(results):
            z.write(r, f"compressed_{i+1}.pdf")
    cleanup(*results)
    return file_response(zip_path, "compressed.zip", "application/zip")
