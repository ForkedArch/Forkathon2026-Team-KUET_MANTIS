import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException

# Only allow image types we actually expect for item photos. This prevents
# someone uploading e.g. an .html or .svg file that later gets served back
# by the /uploads static mount (potential stored XSS), and stops arbitrary
# file types from being written to disk.
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


async def save_upload_file(upload_file: UploadFile, upload_dir: str) -> str:
    # Validate declared content-type and extension.
    content_type = (upload_file.content_type or "").lower()
    ext = os.path.splitext(upload_file.filename or "")[1].lower()

    if content_type not in ALLOWED_CONTENT_TYPES or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only JPEG, PNG, and WEBP images are allowed.",
        )

    # Normalize the extension based on the content-type rather than trusting
    # the client-supplied filename extension verbatim.
    ext = ALLOWED_CONTENT_TYPES[content_type]

    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, filename)

    # Enforce a max size while streaming to disk, instead of trusting
    # Content-Length or reading the whole file into memory first.
    size = 0
    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await upload_file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=400,
                        detail="File too large. Max upload size is 5 MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        # Clean up the partial file before re-raising.
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    finally:
        await upload_file.close()

    return f"/uploads/{filename}"
