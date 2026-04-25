from typing import List, Optional

from pydantic import BaseModel


class SectionInfo(BaseModel):
    id: str
    placeholder: str
    flag_name: str
    title: str
    required_styles: List[str] = []


class ParsedStructure(BaseModel):
    context_vars: List[str] = []
    sections: List[SectionInfo] = []
    attachments_bundle: Optional[dict] = None
    required_styles: List[str] = []


class TemplateResponse(BaseModel):
    id: str
    name: str
    original_filename: str
    parsed_structure: ParsedStructure
    created_at: str

    class Config:
        from_attributes = True


class TemplateUploadResponse(BaseModel):
    id: str
    name: str
    warnings: List[str] = []
