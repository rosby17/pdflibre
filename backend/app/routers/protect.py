from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import pypdf
from app.utils.files import tmp_path, cleanup, file_response

router = APIRouter()

@router.post("")
async def protect_pdf(
    files: List[UploadFile] = File(...),
    password: str = Form(...),
    permissions: str = Form("readonly"),  # readonly | print | copy
):
    if not password:
        raise HTTPException(400, "Mot de passe requis")

    # Build permission flags
    perm_flags = pypdf.generic.PAGE_FIT  # default restricted
    allow_print = "print" in permissions
    allow_copy  = "copy"  in permissions

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

            writer.encrypt(
                user_password=password,
                owner_password=password + "_owner",
                use_128bit=True,
                permissions_flag=pypdf.generic.PermissionsFlag.PRINT if allow_print else 0
                    | pypdf.generic.PermissionsFlag.COPY_DOC_CONTENTS if allow_copy else 0,
            )

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
        return file_response(out, name.replace(".pdf", "_protected.pdf"))

    import zipfile
    zip_path = tmp_path(".zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for out, name in results:
            z.write(out, name.replace(".pdf", "_protected.pdf"))
    cleanup(*[r[0] for r in results])
    return file_response(zip_path, "protected.zip", "application/zip")
