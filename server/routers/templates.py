import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from server.config import TEMPLATES_DIR
from server.database import get_db
from server.models.template import Template
from server.schemas.template import TemplateResponse, TemplateUploadResponse
from server.services.auth_service import get_current_user
from server.services.template_parser import parse_template

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _auth(authorization: str, db: Session):
    token = authorization.replace("Bearer ", "")
    try:
        return get_current_user(db, token)
    except ValueError:
        raise HTTPException(401, "Invalid token")


@router.post("", response_model=TemplateUploadResponse, status_code=201)
async def upload_template(
    file: UploadFile = File(...),
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    if not file.filename.endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")

    template_id = str(uuid.uuid4())
    file_path = TEMPLATES_DIR / f"{template_id}.docx"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        structure, warnings = parse_template(str(file_path))
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(422, f"Failed to parse template: {e}")

    if not structure["sections"] and not structure["attachments_bundle"]:
        file_path.unlink(missing_ok=True)
        raise HTTPException(422, "No recognizable sections in template")

    name = file.filename.replace(".docx", "")
    tmpl = Template(
        id=template_id,
        user_id=user.id,
        name=name,
        original_filename=file.filename,
        file_path=str(file_path),
        parsed_structure=structure,
    )
    db.add(tmpl)
    db.commit()

    return TemplateUploadResponse(id=template_id, name=name, warnings=warnings)


@router.get("", response_model=list[TemplateResponse])
def list_templates(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    templates = (
        db.query(Template)
        .filter(Template.user_id == user.id)
        .order_by(Template.created_at.desc())
        .all()
    )
    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            original_filename=t.original_filename,
            parsed_structure=t.parsed_structure,
            created_at=t.created_at.isoformat(),
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    tmpl = (
        db.query(Template)
        .filter(Template.id == template_id, Template.user_id == user.id)
        .first()
    )
    if not tmpl:
        raise HTTPException(404, "Template not found")
    return TemplateResponse(
        id=tmpl.id,
        name=tmpl.name,
        original_filename=tmpl.original_filename,
        parsed_structure=tmpl.parsed_structure,
        created_at=tmpl.created_at.isoformat(),
    )


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    tmpl = (
        db.query(Template)
        .filter(Template.id == template_id, Template.user_id == user.id)
        .first()
    )
    if not tmpl:
        raise HTTPException(404, "Template not found")
    Path(tmpl.file_path).unlink(missing_ok=True)
    db.delete(tmpl)
    db.commit()
