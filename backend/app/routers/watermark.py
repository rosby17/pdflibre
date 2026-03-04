from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import pypdf
from pypdf import PdfWriter, PdfReader
from pypdf.generic import (
    ArrayObject, FloatObject, NameObject,
    RectangleObject, ContentStream, DecodedStreamObject
)
import io, math
from app.utils.files import tmp_path, cleanup, file_response

router = APIRouter()

def make_watermark_page(text: str, opacity: float, width: float, height: float) -> pypdf.PageObject:
    """Create an in-memory PDF page with diagonal text watermark."""
    # Build a minimal PDF watermark using reportlab if available, else fallback to text overlay
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.colors import Color

        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=(width, height))
        c.setFont("Helvetica-Bold", min(width, height) / 10)
        r, g, b = 0.78, 0.24, 0.04  # terracotta accent
        c.setFillColor(Color(r, g, b, alpha=opacity))
        c.saveState()
        c.translate(width / 2, height / 2)
        c.rotate(35)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        c.save()

        buf.seek(0)
        wm_reader = PdfReader(buf)
        return wm_reader.pages[0]

    except ImportError:
        # Fallback: plain text via content stream (no color/opacity control)
        raise HTTPException(500, "reportlab requis pour le filigrane — installez-le via pip")


@router.post("")
async def watermark_pdf(
    files: List[UploadFile] = File(...),
    text: str    = Form("CONFIDENTIEL"),
    opacity: int = Form(25),
    position: str = Form("diagonal"),
):
    alpha = max(0.05, min(0.8, opacity / 100))
    results = []

    for upload in files:
        src = tmp_path(".pdf")
        out = tmp_path(".pdf")
        try:
            src.write_bytes(await upload.read())
            reader = PdfReader(str(src))
            writer = PdfWriter()

            for page in reader.pages:
                box = page.mediabox
                w = float(box.width)
                h = float(box.height)

                wm_page = make_watermark_page(text, alpha, w, h)

                page.merge_page(wm_page)
                writer.add_page(page)

            with open(out, "wb") as fh:
                writer.write(fh)

            results.append((out, upload.filename))
        except HTTPException:
            raise
        except Exception as e:
            cleanup(src, out)
            raise HTTPException(500, str(e))
        finally:
            cleanup(src)

    if len(results) == 1:
        out, name = results[0]
        return file_response(out, name.replace(".pdf", "_watermarked.pdf"))

    import zipfile
    zip_path = tmp_path(".zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for out, name in results:
            z.write(out, name.replace(".pdf", "_watermarked.pdf"))
    cleanup(*[r[0] for r in results])
    return file_response(zip_path, "watermarked.zip", "application/zip")
