from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from PIL import Image
import io
from app.utils.files import tmp_path, cleanup, file_response

router = APIRouter()

PAGE_SIZES = {
    "a4":    (595, 842),
    "letter":(612, 792),
    "fit":   None,
}

@router.post("")
async def jpg_to_pdf(
    files: List[UploadFile] = File(...),
    page_format: str = Form("a4"),   # a4 | letter | fit
    margins: bool = Form(True),
):
    if not files:
        raise HTTPException(400, "Aucune image fournie")

    size = PAGE_SIZES.get(page_format.lower(), (595, 842))
    margin = 28 if margins else 0  # ~10mm in points
    out = tmp_path(".pdf")

    try:
        pil_images = []
        for upload in files:
            data = await upload.read()
            img = Image.open(io.BytesIO(data)).convert("RGB")

            if size:  # fixed page — fit image inside with margins
                pw, ph = size
                iw, ih = img.size
                max_w = pw - 2 * margin
                max_h = ph - 2 * margin
                scale = min(max_w / iw, max_h / ih)
                new_w = int(iw * scale)
                new_h = int(ih * scale)
                img = img.resize((new_w, new_h), Image.LANCZOS)

                canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
                x = (pw - new_w) // 2
                y = (ph - new_h) // 2
                canvas.paste(img, (x, y))
                pil_images.append(canvas)
            else:
                # fit to image size
                pil_images.append(img)

        pil_images[0].save(
            str(out), "PDF", resolution=150,
            save_all=True, append_images=pil_images[1:]
        )

        return file_response(out, "images.pdf")

    except Exception as e:
        cleanup(out)
        raise HTTPException(500, str(e))
