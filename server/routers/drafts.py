from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from server.database import get_db
from server.models.draft import Draft
from server.models.template import Template
from server.schemas.draft import DraftCreate, DraftListItem, DraftResponse, DraftUpdate
from server.services.auth_service import get_current_user
from server.services.draft_service import generate_empty_context, generate_empty_sections
from server.services.export_service import export_draft_to_docx


def _order_sections(sections: dict, parsed_structure: dict) -> dict:
    """Reorder sections dict to match template's original section order."""
    template_order = [s["id"] for s in parsed_structure.get("sections", [])]
    ordered = {}
    for sid in template_order:
        if sid in sections:
            ordered[sid] = sections[sid]
    for sid in sections:
        if sid not in ordered:
            ordered[sid] = sections[sid]
    return ordered

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


def _auth(authorization: str, db: Session):
    token = authorization.replace("Bearer ", "")
    try:
        return get_current_user(db, token)
    except ValueError:
        raise HTTPException(401, "Invalid token")


@router.post("", response_model=DraftResponse, status_code=201)
def create_draft(
    req: DraftCreate,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    tmpl = (
        db.query(Template)
        .filter(Template.id == req.template_id, Template.user_id == user.id)
        .first()
    )
    if not tmpl:
        raise HTTPException(404, "Template not found")
    draft = Draft(
        user_id=user.id,
        template_id=tmpl.id,
        title=req.title,
        context=generate_empty_context(tmpl.parsed_structure),
        sections=generate_empty_sections(tmpl.parsed_structure),
        attachments={},
        section_enabled={s["id"]: True for s in tmpl.parsed_structure.get("sections", [])},
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return DraftResponse(
        id=draft.id,
        template_id=draft.template_id,
        title=draft.title,
        context=draft.context,
        sections=draft.sections,
        attachments=draft.attachments,
        section_enabled=draft.section_enabled,
        status=draft.status,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


@router.get("", response_model=list[DraftListItem])
def list_drafts(
    authorization: str = Header(...), db: Session = Depends(get_db)
):
    user = _auth(authorization, db)
    drafts = (
        db.query(Draft)
        .filter(Draft.user_id == user.id)
        .order_by(Draft.updated_at.desc())
        .all()
    )
    return [
        DraftListItem(
            id=d.id,
            template_id=d.template_id,
            title=d.title,
            status=d.status,
            updated_at=d.updated_at.isoformat(),
        )
        for d in drafts
    ]


@router.get("/{draft_id}", response_model=DraftResponse)
def get_draft(
    draft_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    draft = (
        db.query(Draft)
        .filter(Draft.id == draft_id, Draft.user_id == user.id)
        .first()
    )
    if not draft:
        raise HTTPException(404, "Draft not found")
    tmpl = db.query(Template).filter(Template.id == draft.template_id).first()
    ordered_sections = (
        _order_sections(draft.sections, tmpl.parsed_structure)
        if tmpl
        else draft.sections
    )
    return DraftResponse(
        id=draft.id,
        template_id=draft.template_id,
        title=draft.title,
        context=draft.context,
        sections=ordered_sections,
        attachments=draft.attachments,
        section_enabled=draft.section_enabled,
        status=draft.status,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


@router.patch("/{draft_id}", response_model=DraftResponse)
def update_draft(
    draft_id: str,
    req: DraftUpdate,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    draft = (
        db.query(Draft)
        .filter(Draft.id == draft_id, Draft.user_id == user.id)
        .first()
    )
    if not draft:
        raise HTTPException(404, "Draft not found")
    if req.title is not None:
        draft.title = req.title
    if req.context is not None:
        draft.context = req.context
    if req.sections is not None:
        draft.sections = req.sections
    if req.attachments is not None:
        draft.attachments = req.attachments
    if req.section_enabled is not None:
        draft.section_enabled = req.section_enabled
    draft.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(draft)
    return DraftResponse(
        id=draft.id,
        template_id=draft.template_id,
        title=draft.title,
        context=draft.context,
        sections=draft.sections,
        attachments=draft.attachments,
        section_enabled=draft.section_enabled,
        status=draft.status,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


@router.delete("/{draft_id}", status_code=204)
def delete_draft(
    draft_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    draft = (
        db.query(Draft)
        .filter(Draft.id == draft_id, Draft.user_id == user.id)
        .first()
    )
    if not draft:
        raise HTTPException(404, "Draft not found")
    db.delete(draft)
    db.commit()


@router.post("/{draft_id}/export")
def export_draft(
    draft_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    user = _auth(authorization, db)
    draft = (
        db.query(Draft)
        .filter(Draft.id == draft_id, Draft.user_id == user.id)
        .first()
    )
    if not draft:
        raise HTTPException(404, "Draft not found")
    tmpl = db.query(Template).filter(Template.id == draft.template_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    draft_data = {
        "context": draft.context,
        "sections": draft.sections,
        "attachments": draft.attachments,
        "section_enabled": draft.section_enabled,
    }
    try:
        output_path = export_draft_to_docx(draft_data, tmpl.file_path, tmpl.parsed_structure)
    except Exception as e:
        raise HTTPException(500, f"Export failed: {e}")
    filename = f"{draft.title}.docx"
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )
