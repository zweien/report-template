import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from server.config import UPLOADS_DIR
from server.database import get_db
from server.services.auth_service import get_current_user

router = APIRouter(prefix="/api/upload", tags=["upload"])


def _auth(authorization: str, db: Session):
    token = authorization.replace("Bearer ", "")
    try:
        return get_current_user(db, token)
    except ValueError:
        raise HTTPException(401, "Invalid token")


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    _auth(authorization, db)

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "png"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = UPLOADS_DIR / filename

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"url": f"/api/upload/files/{filename}", "filename": filename}


@router.get("/files/{filename}")
def get_file(filename: str):
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)
