from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DraftCreate(BaseModel):
    template_id: str
    title: str = "Untitled"


class DraftUpdate(BaseModel):
    title: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    sections: Optional[Dict[str, Any]] = None
    attachments: Optional[Dict[str, Any]] = None


class DraftResponse(BaseModel):
    id: str
    template_id: str
    title: str
    context: Dict[str, Any]
    sections: Dict[str, Any]
    attachments: Dict[str, Any]
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DraftListItem(BaseModel):
    id: str
    template_id: str
    title: str
    status: str
    updated_at: str
