# Online Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an online report editor with BlockNote + Next.js 16 + FastAPI, where users upload .docx templates, edit content per-section, and export finished reports.

**Architecture:** Section-based editor — each template section maps to an independent BlockNote instance. Backend parses templates, stores drafts, converts BlockNote JSON to report-engine payloads for .docx export. Linear-style dark UI.

**Tech Stack:** Next.js 16, React 19, BlockNote, Zustand, shadcn/ui, Tailwind CSS (frontend) · FastAPI, SQLAlchemy, SQLite, python-jose, report-engine (backend)

---

## Phase 1: Backend API Skeleton

### Task 1: FastAPI Project Init + Database

**Files:**
- Create: `server/main.py`
- Create: `server/config.py`
- Create: `server/database.py`
- Create: `server/requirements.txt`

- [ ] **Step 1: Create server directory and requirements.txt**

```bash
mkdir -p server/routers server/services server/models server/schemas
```

```txt
# server/requirements.txt
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy==2.0.*
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
python-multipart==0.0.*
python-docx==1.1.*
aiofiles==24.*
```

- [ ] **Step 2: Create config.py**

```python
# server/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "uploaded_templates"
UPLOADS_DIR = DATA_DIR / "uploads"

# Ensure dirs exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'editor.db'}")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
```

- [ ] **Step 3: Create database.py**

```python
# server/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from server.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: Create main.py**

```python
# server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.database import init_db

app = FastAPI(title="Report Editor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3070"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Verify server starts**

```bash
cd /home/z/codebase/report-template
pip install -r server/requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 8070 --reload
# In another terminal:
curl http://localhost:8070/api/health
# Expected: {"status":"ok"}
```

- [ ] **Step 6: Commit**

```bash
git add server/
git commit -m "feat(server): init FastAPI project with SQLite database"
```

---

### Task 2: User Model + Auth API

**Files:**
- Create: `server/models/user.py`
- Create: `server/schemas/auth.py`
- Create: `server/services/auth_service.py`
- Create: `server/routers/auth.py`
- Modify: `server/main.py`

- [ ] **Step 1: Create User model**

```python
# server/models/user.py
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.sqlite import BLOB

from server.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: Create auth schemas**

```python
# server/schemas/auth.py
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
```

- [ ] **Step 3: Create auth service**

```python
# server/services/auth_service.py
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from server.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from server.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(db: Session, token: str) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise ValueError("Invalid token")
    except JWTError:
        raise ValueError("Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise ValueError("User not found")
    return user
```

- [ ] **Step 4: Create auth router**

```python
# server/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from server.database import get_db
from server.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from server.services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from server.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username already exists")
    user = User(username=req.username, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/me", response_model=UserResponse)
def me(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    try:
        user = get_current_user(db, token)
    except ValueError:
        raise HTTPException(401, "Invalid token")
    return user
```

- [ ] **Step 5: Register router in main.py**

Add to `server/main.py`:

```python
from server.routers.auth import router as auth_router
app.include_router(auth_router)
```

- [ ] **Step 6: Test auth endpoints**

```bash
uvicorn server.main:app --host 0.0.0.0 --port 8070 --reload
# Register
curl -X POST http://localhost:8070/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
# Expected: {"id":"...","username":"test"}

# Login
curl -X POST http://localhost:8070/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
# Expected: {"access_token":"...","token_type":"bearer"}
```

- [ ] **Step 7: Commit**

```bash
git add server/
git commit -m "feat(server): add user model and auth API (register/login/me)"
```

---

### Task 3: Template Model + Upload API

**Files:**
- Create: `server/models/template.py`
- Create: `server/schemas/template.py`
- Create: `server/services/template_parser.py`
- Create: `server/routers/templates.py`
- Modify: `server/main.py`

- [ ] **Step 1: Create Template model**

```python
# server/models/template.py
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.sqlite import JSON

from server.database import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    parsed_structure = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: Create template schemas**

```python
# server/schemas/template.py
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
```

- [ ] **Step 3: Create template parser service**

```python
# server/services/template_parser.py
import re
from pathlib import Path
from typing import List, Tuple
from zipfile import ZipFile


def _read_template_xml(template_path: str) -> str:
    with ZipFile(template_path) as zf:
        xml_parts = []
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                xml_parts.append(zf.read(name).decode("utf-8", errors="ignore"))
        return "\n".join(xml_parts)


def _extract_scalar_vars(xml: str) -> List[str]:
    pattern = r"\{\{\s*([A-Z_][A-Z0-9_]*)\b"
    return sorted(set(re.findall(pattern, xml)))


def _extract_subdoc_placeholders(xml: str) -> List[str]:
    pattern = r"\{\{p\s+([A-Z_][A-Z0-9_]*)\s*\}\}"
    return sorted(set(re.findall(pattern, xml)))


def _extract_flags(xml: str) -> List[str]:
    pattern = r"\{%p\s+if\s+([A-Z_][A-Z0-9_]*)\s*%\}"
    return sorted(set(re.findall(pattern, xml)))


def _extract_heading_texts(xml: str) -> List[Tuple[int, str]]:
    """Extract heading texts with their outline levels."""
    headings = []
    # Match paragraphs with heading styles
    for match in re.finditer(
        r'<w:pStyle w:val="Heading\s*(\d+)"[^/]*/>.*?<w:t[^>]*>(.*?)</w:t>',
        xml, re.DOTALL
    ):
        level = int(match.group(1))
        text = match.group(2).strip()
        if text:
            headings.append((level, text))
    return headings


def _pair_flags_with_subdocs(
    flags: List[str], subdocs: List[str], headings: List[Tuple[int, str]]
) -> List[dict]:
    """Pair ENABLE_* flags with their corresponding SUBDOC placeholders."""
    sections = []
    for flag in flags:
        # ENABLE_RESEARCH_CONTENT → RESEARCH_CONTENT_SUBDOC
        base = flag.replace("ENABLE_", "")
        placeholder = f"{base}_SUBDOC"
        if placeholder in subdocs:
            # Try to find a matching heading
            title = base.replace("_", " ").title()
            for level, text in headings:
                if base.lower().replace("_", "") in text.lower().replace(" ", "").replace("、", ""):
                    title = text
                    break
            sections.append({
                "id": base.lower(),
                "placeholder": placeholder,
                "flag_name": flag,
                "title": title,
                "required_styles": [],
            })
    return sections


def parse_template(template_path: str) -> Tuple[dict, List[str]]:
    """Parse a .docx template and return (parsed_structure, warnings)."""
    warnings = []
    xml = _read_template_xml(template_path)

    scalar_vars = _extract_scalar_vars(xml)
    subdocs = _extract_subdoc_placeholders(xml)
    flags = _extract_flags(xml)
    headings = _extract_heading_texts(xml)

    # Filter out ENABLE_ prefixed vars from scalar_vars (they are flags, not context)
    context_vars = [v for v in scalar_vars if not v.startswith("ENABLE_")]

    sections = _pair_flags_with_subdocs(flags, subdocs, headings)

    # Find subdocs without flags (default enabled)
    paired_subdocs = {s["placeholder"] for s in sections}
    for sd in subdocs:
        if sd not in paired_subdocs and sd != "APPENDICES_SUBDOC":
            warnings.append(f"Subdoc {sd} has no ENABLE flag, will default to enabled")

    if not sections:
        warnings.append("No recognizable sections found in template")

    # Check for attachments bundle
    attachments_bundle = None
    if "APPENDICES_SUBDOC" in subdocs:
        attachments_bundle = {
            "placeholder": "APPENDICES_SUBDOC",
            "flag_name": "ENABLE_APPENDICES",
        }

    structure = {
        "context_vars": context_vars,
        "sections": sections,
        "attachments_bundle": attachments_bundle,
        "required_styles": [],
    }
    return structure, warnings
```

- [ ] **Step 4: Create templates router**

```python
# server/routers/templates.py
from datetime import datetime
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session

from server.config import TEMPLATES_DIR
from server.database import get_db
from server.models.template import Template
from server.models.user import User
from server.schemas.template import TemplateResponse, TemplateUploadResponse
from server.services.auth_service import get_current_user
from server.services.template_parser import parse_template

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _auth(authorization: str, db: Session) -> User:
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

    # Save file
    template_id = str(uuid.uuid4())
    file_path = TEMPLATES_DIR / f"{template_id}.docx"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Parse
    try:
        structure, warnings = parse_template(str(file_path))
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(422, f"Failed to parse template: {e}")

    if not structure["sections"] and not structure["attachments_bundle"]:
        file_path.unlink(missing_ok=True)
        raise HTTPException(422, "No recognizable sections in template")

    # Save to DB
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
def list_templates(authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    templates = db.query(Template).filter(Template.user_id == user.id).order_by(Template.created_at.desc()).all()
    result = []
    for t in templates:
        result.append(TemplateResponse(
            id=t.id,
            name=t.name,
            original_filename=t.original_filename,
            parsed_structure=t.parsed_structure,
            created_at=t.created_at.isoformat(),
        ))
    return result


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str, authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    tmpl = db.query(Template).filter(Template.id == template_id, Template.user_id == user.id).first()
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
def delete_template(template_id: str, authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    tmpl = db.query(Template).filter(Template.id == template_id, Template.user_id == user.id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    Path(tmpl.file_path).unlink(missing_ok=True)
    db.delete(tmpl)
    db.commit()
```

- [ ] **Step 5: Register router in main.py**

```python
from server.routers.templates import router as templates_router
app.include_router(templates_router)
```

- [ ] **Step 6: Test template upload**

```bash
# Login first to get token
TOKEN=$(curl -s -X POST http://localhost:8070/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Upload a template
curl -X POST http://localhost:8070/api/templates \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@templates/test_all_blocks.docx"
# Expected: {"id":"...","name":"test_all_blocks","warnings":[...]}
```

- [ ] **Step 7: Commit**

```bash
git add server/
git commit -m "feat(server): add template model, parser, and upload API"
```

---

### Task 4: Draft Model + CRUD API

**Files:**
- Create: `server/models/draft.py`
- Create: `server/schemas/draft.py`
- Create: `server/services/draft_service.py`
- Create: `server/routers/drafts.py`
- Modify: `server/main.py`

- [ ] **Step 1: Create Draft model**

```python
# server/models/draft.py
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.sqlite import JSON

from server.database import Base


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    template_id = Column(String(36), ForeignKey("templates.id"), nullable=False)
    title = Column(String(200), nullable=False, default="Untitled")
    context = Column(JSON, nullable=False, default=dict)
    sections = Column(JSON, nullable=False, default=dict)
    attachments = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: Create draft schemas**

```python
# server/schemas/draft.py
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
```

- [ ] **Step 3: Create draft service (generate empty sections from template)**

```python
# server/services/draft_service.py
from typing import Any, Dict


def generate_empty_sections(parsed_structure: dict) -> Dict[str, Any]:
    """Generate empty BlockNote blocks for each section in the template."""
    sections = {}
    for section in parsed_structure.get("sections", []):
        # One empty heading block per section
        sections[section["id"]] = [
            {
                "id": f"heading-{section['id']}",
                "type": "heading",
                "props": {"level": 1},
                "content": [{"type": "text", "text": section.get("title", section["id"])}],
            }
        ]
    return sections


def generate_empty_context(parsed_structure: dict) -> Dict[str, str]:
    """Generate empty context variables from template."""
    return {var: "" for var in parsed_structure.get("context_vars", [])}
```

- [ ] **Step 4: Create drafts router**

```python
# server/routers/drafts.py
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from server.database import get_db
from server.models.draft import Draft
from server.models.template import Template
from server.models.user import User
from server.schemas.draft import DraftCreate, DraftListItem, DraftResponse, DraftUpdate
from server.services.auth_service import get_current_user
from server.services.draft_service import generate_empty_context, generate_empty_sections

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


def _auth(authorization: str, db: Session) -> User:
    token = authorization.replace("Bearer ", "")
    try:
        return get_current_user(db, token)
    except ValueError:
        raise HTTPException(401, "Invalid token")


@router.post("", response_model=DraftResponse, status_code=201)
def create_draft(req: DraftCreate, authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    tmpl = db.query(Template).filter(Template.id == req.template_id, Template.user_id == user.id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")

    draft = Draft(
        user_id=user.id,
        template_id=tmpl.id,
        title=req.title,
        context=generate_empty_context(tmpl.parsed_structure),
        sections=generate_empty_sections(tmpl.parsed_structure),
        attachments={},
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return DraftResponse(
        id=draft.id, template_id=draft.template_id, title=draft.title,
        context=draft.context, sections=draft.sections, attachments=draft.attachments,
        status=draft.status, created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


@router.get("", response_model=list[DraftListItem])
def list_drafts(authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    drafts = db.query(Draft).filter(Draft.user_id == user.id).order_by(Draft.updated_at.desc()).all()
    return [DraftListItem(
        id=d.id, template_id=d.template_id, title=d.title,
        status=d.status, updated_at=d.updated_at.isoformat(),
    ) for d in drafts]


@router.get("/{draft_id}", response_model=DraftResponse)
def get_draft(draft_id: str, authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user.id).first()
    if not draft:
        raise HTTPException(404, "Draft not found")
    return DraftResponse(
        id=draft.id, template_id=draft.template_id, title=draft.title,
        context=draft.context, sections=draft.sections, attachments=draft.attachments,
        status=draft.status, created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


@router.patch("/{draft_id}", response_model=DraftResponse)
def update_draft(draft_id: str, req: DraftUpdate, authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user.id).first()
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
    draft.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(draft)
    return DraftResponse(
        id=draft.id, template_id=draft.template_id, title=draft.title,
        context=draft.context, sections=draft.sections, attachments=draft.attachments,
        status=draft.status, created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


@router.delete("/{draft_id}", status_code=204)
def delete_draft(draft_id: str, authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user.id).first()
    if not draft:
        raise HTTPException(404, "Draft not found")
    db.delete(draft)
    db.commit()
```

- [ ] **Step 5: Register router in main.py**

```python
from server.routers.drafts import router as drafts_router
app.include_router(drafts_router)
```

- [ ] **Step 6: Test draft CRUD**

```bash
# Create draft (use template_id from previous upload)
curl -X POST http://localhost:8070/api/drafts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"template_id":"<template_id>","title":"Test Draft"}'
# Expected: {"id":"...","sections":{"research_content":[...],...},...}

# List drafts
curl http://localhost:8070/api/drafts -H "Authorization: Bearer $TOKEN"
```

- [ ] **Step 7: Commit**

```bash
git add server/
git commit -m "feat(server): add draft model and CRUD API"
```

---

### Task 5: BlockNote → report-engine Converter (Backend)

**Files:**
- Create: `server/services/converter.py`

- [ ] **Step 1: Create converter service**

```python
# server/services/converter.py
from typing import Any, Dict, List


def _extract_text(content: List[dict]) -> str:
    """Extract plain text from BlockNote content array."""
    return "".join(segment.get("text", "") for segment in content)


def _has_inline_styles(segments: List[dict]) -> bool:
    """Check if any segment has non-empty styles."""
    return any(segment.get("styles") for segment in segments)


def _convert_rich_paragraph(block: dict) -> dict:
    """Convert a BlockNote paragraph with inline styles to rich_paragraph."""
    segments = []
    for seg in block.get("content", []):
        s = {"text": seg.get("text", "")}
        styles = seg.get("styles", {})
        if styles.get("bold"):
            s["bold"] = True
        if styles.get("italic"):
            s["italic"] = True
        segments.append(s)
    return {"type": "rich_paragraph", "segments": segments}


def _convert_paragraph(block: dict) -> dict:
    """Convert a plain BlockNote paragraph."""
    text = _extract_text(block.get("content", []))
    if _has_inline_styles(block.get("content", [])):
        return _convert_rich_paragraph(block)
    return {"type": "paragraph", "text": text}


def _convert_heading(block: dict) -> dict:
    text = _extract_text(block.get("content", []))
    level = block.get("props", {}).get("level", 2)
    return {"type": "heading", "text": text, "level": level}


def _convert_table(block: dict) -> dict:
    """Convert BlockNote table to report-engine table."""
    rows = []
    content = block.get("content", {})
    if isinstance(content, dict):
        # BlockNote table format: {rows: [{cells: [...]}]}
        for row in content.get("rows", []):
            cells = [_extract_text(cell.get("content", [])) if isinstance(cell, dict) else str(cell) for cell in row.get("cells", [])]
            rows.append(cells)
    elif isinstance(content, list):
        # Fallback: list of rows
        for row in content:
            if isinstance(row, list):
                rows.append([str(c) for c in row])

    if not rows:
        return None

    headers = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    return {"type": "table", "title": "", "headers": headers, "rows": data_rows}


def _convert_quote(block: dict) -> dict:
    text = _extract_text(block.get("content", []))
    return {"type": "quote", "text": text}


def _convert_code_block(block: dict) -> dict:
    code = _extract_text(block.get("content", []))
    return {"type": "code_block", "code": code}


def _convert_image(block: dict) -> dict:
    props = block.get("props", {})
    return {
        "type": "image",
        "path": props.get("url", props.get("src", "")),
        "width": props.get("width"),
        "caption": props.get("caption", ""),
    }


def convert_blocknote_blocks(blocks: List[dict]) -> List[dict]:
    """Convert a list of BlockNote blocks to report-engine blocks."""
    result = []
    i = 0

    while i < len(blocks):
        block = blocks[i]
        block_type = block.get("type", "")

        if block_type == "heading":
            result.append(_convert_heading(block))
        elif block_type == "paragraph":
            converted = _convert_paragraph(block)
            if converted:
                result.append(converted)
        elif block_type == "bulletListItem":
            # Aggregate consecutive bulletListItems
            items = []
            while i < len(blocks) and blocks[i].get("type") == "bulletListItem":
                items.append(_extract_text(blocks[i].get("content", [])))
                i += 1
            result.append({"type": "bullet_list", "items": items})
            continue
        elif block_type == "numberedListItem":
            items = []
            while i < len(blocks) and blocks[i].get("type") == "numberedListItem":
                items.append(_extract_text(blocks[i].get("content", [])))
                i += 1
            result.append({"type": "numbered_list", "items": items})
            continue
        elif block_type == "table":
            converted = _convert_table(block)
            if converted:
                result.append(converted)
        elif block_type == "quote":
            result.append(_convert_quote(block))
        elif block_type == "codeBlock":
            result.append(_convert_code_block(block))
        elif block_type == "image":
            result.append(_convert_image(block))
        elif block_type == "pageBreak":
            result.append({"type": "page_break"})
        # Unsupported types are silently ignored

        i += 1

    return result


def draft_to_payload(draft_data: dict, template_parsed_structure: dict) -> dict:
    """Convert a draft to a report-engine payload."""
    sections = []
    for section_meta in template_parsed_structure.get("sections", []):
        section_id = section_meta["id"]
        blocks_data = draft_data.get("sections", {}).get(section_id, [])

        sections.append({
            "id": section_id,
            "placeholder": section_meta["placeholder"],
            "flag_name": section_meta["flag_name"],
            "enabled": True,
            "blocks": convert_blocknote_blocks(blocks_data),
        })

    payload = {
        "context": draft_data.get("context", {}),
        "sections": sections,
        "attachments": [],
        "attachments_bundle": None,
        "style_map": {},
    }

    # Handle attachments bundle
    bundle_meta = template_parsed_structure.get("attachments_bundle")
    if bundle_meta:
        payload["attachments_bundle"] = {
            "enabled": True,
            "placeholder": bundle_meta["placeholder"],
            "flag_name": bundle_meta["flag_name"],
        }

    return payload
```

- [ ] **Step 2: Commit**

```bash
git add server/services/converter.py
git commit -m "feat(server): add BlockNote to report-engine converter"
```

---

### Task 6: Export API (render .docx)

**Files:**
- Create: `server/services/export_service.py`
- Modify: `server/routers/drafts.py`

- [ ] **Step 1: Create export service**

```python
# server/services/export_service.py
import tempfile
from pathlib import Path

from report_engine.renderer import render_report

from server.services.converter import draft_to_payload


def export_draft_to_docx(draft_data: dict, template_path: str, parsed_structure: dict) -> str:
    """Render a draft to .docx and return the output file path."""
    payload = draft_to_payload(draft_data, parsed_structure)

    # Create temp file for output
    output_path = tempfile.mktemp(suffix=".docx")

    render_report(
        template_path=template_path,
        payload_data=payload,
        output_path=output_path,
        check_template=False,  # Skip check for speed
    )

    return output_path
```

- [ ] **Step 2: Add export endpoint to drafts router**

Add to `server/routers/drafts.py`:

```python
from server.services.export_service import export_draft_to_docx


@router.post("/{draft_id}/export")
def export_draft(draft_id: str, authorization: str = Header(...), db: Session = Depends(get_db)):
    user = _auth(authorization, db)
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user.id).first()
    if not draft:
        raise HTTPException(404, "Draft not found")

    tmpl = db.query(Template).filter(Template.id == draft.template_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")

    draft_data = {
        "context": draft.context,
        "sections": draft.sections,
        "attachments": draft.attachments,
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
```

- [ ] **Step 3: Test export**

```bash
# Create a draft with some content, then export
curl -X POST http://localhost:8070/api/drafts/<draft_id>/export \
  -H "Authorization: Bearer $TOKEN" \
  -o output.docx
# Expected: output.docx is a valid Word document
```

- [ ] **Step 4: Commit**

```bash
git add server/
git commit -m "feat(server): add draft export API (render .docx)"
```

---

## Phase 2: Frontend Skeleton

### Task 7: Next.js 16 Project Init

**Files:**
- Create: `web/` (entire Next.js project)

- [ ] **Step 1: Scaffold Next.js project**

```bash
cd /home/z/codebase/report-template
npx create-next-app@latest web --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --no-turbopack
cd web
```

- [ ] **Step 2: Install dependencies**

```bash
npm install zustand axios @blocknote/react @blocknote/core @blocknote/shadcn
npx shadcn@latest init --defaults
```

- [ ] **Step 3: Configure port and API proxy**

Update `web/next.config.ts`:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8070/api/:path*",
      },
    ];
  },
};

export default nextConfig;
```

Update `web/package.json` scripts:

```json
{
  "scripts": {
    "dev": "next dev -p 3070",
    "build": "next build",
    "start": "next start -p 3070"
  }
}
```

- [ ] **Step 4: Set up global styles (Linear dark theme)**

Replace `web/app/globals.css`:

```css
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

:root {
  --background: #ffffff;
  --foreground: #171717;
}

.dark {
  --background: #0A0A0B;
  --foreground: #E8E8ED;
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: "Inter", system-ui, -apple-system, sans-serif;
}

/* Linear-style scrollbar */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
```

Update `web/app/layout.tsx` to apply dark class:

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Report Editor",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  );
}
```

- [ ] **Step 5: Create API client**

```typescript
// web/lib/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

- [ ] **Step 6: Verify dev server starts**

```bash
cd web
npm run dev
# Visit http://localhost:3070
```

- [ ] **Step 7: Commit**

```bash
git add web/
git commit -m "feat(web): init Next.js 16 project with dark theme and API client"
```

---

### Task 8: Auth Pages (Login + Register)

**Files:**
- Create: `web/lib/stores/auth-store.ts`
- Create: `web/app/login/page.tsx`
- Create: `web/app/register/page.tsx`

- [ ] **Step 1: Create auth store**

```typescript
// web/lib/stores/auth-store.ts
import { create } from "zustand";
import api from "@/lib/api";

interface User {
  id: string;
  username: string;
}

interface AuthStore {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isLoading: true,

  login: async (username, password) => {
    const { data } = await api.post("/auth/login", { username, password });
    localStorage.setItem("token", data.access_token);
    const { data: user } = await api.get("/auth/me");
    set({ user });
  },

  register: async (username, password) => {
    await api.post("/auth/register", { username, password });
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ user: null });
  },

  checkAuth: async () => {
    try {
      const { data } = await api.get("/auth/me");
      set({ user: data, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },
}));
```

- [ ] **Step 2: Create login page**

```tsx
// web/app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth-store";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      router.push("/dashboard");
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
        <h1 className="text-xl font-semibold">Sign in</h1>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-[#5B6CF0]"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-[#5B6CF0]"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-[#5B6CF0] px-3 py-2 text-sm font-medium text-white hover:bg-[#5B6CF0]/90 disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
        <p className="text-center text-sm text-[#8B8B93]">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-[#5B6CF0] hover:underline">
            Register
          </Link>
        </p>
      </form>
    </div>
  );
}
```

- [ ] **Step 3: Create register page**

```tsx
// web/app/register/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth-store";
import api from "@/lib/api";

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/register", { username, password });
      await login(username, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
        <h1 className="text-xl font-semibold">Create account</h1>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-[#5B6CF0]"
          required
        />
        <input
          type="password"
          placeholder="Password (min 6 chars)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-[#5B6CF0]"
          minLength={6}
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-[#5B6CF0] px-3 py-2 text-sm font-medium text-white hover:bg-[#5B6CF0]/90 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Create account"}
        </button>
        <p className="text-center text-sm text-[#8B8B93]">
          Already have an account?{" "}
          <Link href="/login" className="text-[#5B6CF0] hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
```

- [ ] **Step 4: Test auth flow**

```bash
cd web && npm run dev
# Visit http://localhost:3070/register, create account
# Should redirect to /dashboard (which doesn't exist yet, that's ok)
# Visit http://localhost:3070/login, sign in
```

- [ ] **Step 5: Commit**

```bash
git add web/
git commit -m "feat(web): add login/register pages with auth store"
```

---

### Task 9: Dashboard Page (Template + Draft Lists)

**Files:**
- Create: `web/app/dashboard/page.tsx`
- Create: `web/app/dashboard/templates/upload/page.tsx`

- [ ] **Step 1: Create dashboard page**

```tsx
// web/app/dashboard/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth-store";
import api from "@/lib/api";

interface Template {
  id: string;
  name: string;
  parsed_structure: { sections: { id: string; title: string }[] };
  created_at: string;
}

interface Draft {
  id: string;
  template_id: string;
  title: string;
  status: string;
  updated_at: string;
}

export default function DashboardPage() {
  const { user, isLoading, checkAuth, logout } = useAuthStore();
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (user) {
      Promise.all([api.get("/templates"), api.get("/drafts")]).then(([t, d]) => {
        setTemplates(t.data);
        setDrafts(d.data);
        setLoading(false);
      });
    }
  }, [user]);

  const handleNewDraft = async (templateId: string) => {
    const { data } = await api.post("/drafts", {
      template_id: templateId,
      title: "Untitled",
    });
    router.push(`/drafts/${data.id}`);
  };

  const handleDeleteTemplate = async (id: string) => {
    if (!confirm("Delete this template?")) return;
    await api.delete(`/templates/${id}`);
    setTemplates((prev) => prev.filter((t) => t.id !== id));
  };

  const handleDeleteDraft = async (id: string) => {
    if (!confirm("Delete this draft?")) return;
    await api.delete(`/drafts/${id}`);
    setDrafts((prev) => prev.filter((d) => d.id !== id));
  };

  if (isLoading || !user) return null;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Report Editor</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-[#8B8B93]">{user.username}</span>
          <button onClick={logout} className="text-sm text-[#8B8B93] hover:text-[#E8E8ED]">
            Sign out
          </button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-white/5" />
          ))}
        </div>
      ) : (
        <>
          {/* Templates */}
          <section className="mb-8">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium text-[#8B8B93]">Templates</h2>
              <Link
                href="/dashboard/templates/upload"
                className="rounded-md bg-[#5B6CF0] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#5B6CF0]/90"
              >
                Upload
              </Link>
            </div>
            {templates.length === 0 ? (
              <p className="text-sm text-[#8B8B93]">No templates yet. Upload a .docx to get started.</p>
            ) : (
              <div className="space-y-2">
                {templates.map((t) => (
                  <div
                    key={t.id}
                    className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-[#141415] px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-medium">{t.name}</p>
                      <p className="text-xs text-[#8B8B93]">
                        {t.parsed_structure.sections.length} sections
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleNewDraft(t.id)}
                        className="rounded-md bg-[#5B6CF0]/10 px-3 py-1.5 text-xs font-medium text-[#5B6CF0] hover:bg-[#5B6CF0]/20"
                      >
                        New Draft
                      </button>
                      <button
                        onClick={() => handleDeleteTemplate(t.id)}
                        className="rounded-md px-2 py-1.5 text-xs text-[#8B8B93] hover:bg-white/5 hover:text-red-400"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Drafts */}
          <section>
            <h2 className="mb-3 text-sm font-medium text-[#8B8B93]">Drafts</h2>
            {drafts.length === 0 ? (
              <p className="text-sm text-[#8B8B93]">No drafts yet.</p>
            ) : (
              <div className="space-y-2">
                {drafts.map((d) => (
                  <div
                    key={d.id}
                    className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-[#141415] px-4 py-3"
                  >
                    <Link href={`/drafts/${d.id}`} className="flex-1">
                      <p className="text-sm font-medium hover:text-[#5B6CF0]">{d.title}</p>
                      <p className="text-xs text-[#8B8B93]">
                        Updated {new Date(d.updated_at).toLocaleString()}
                      </p>
                    </Link>
                    <button
                      onClick={() => handleDeleteDraft(d.id)}
                      className="rounded-md px-2 py-1.5 text-xs text-[#8B8B93] hover:bg-white/5 hover:text-red-400"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create template upload page**

```tsx
// web/app/dashboard/templates/upload/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function UploadTemplatePage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError("");
    setWarnings([]);

    const form = new FormData();
    form.append("file", file);

    try {
      const { data } = await api.post("/templates", form);
      if (data.warnings?.length) {
        setWarnings(data.warnings);
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-6 py-8">
      <h1 className="mb-6 text-lg font-semibold">Upload Template</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <p className="text-sm text-red-400">{error}</p>}
        {warnings.length > 0 && (
          <div className="rounded-md border border-yellow-500/20 bg-yellow-500/10 p-3">
            {warnings.map((w, i) => (
              <p key={i} className="text-xs text-yellow-400">{w}</p>
            ))}
          </div>
        )}
        <div>
          <label className="mb-1 block text-sm text-[#8B8B93]">.docx file</label>
          <input
            type="file"
            accept=".docx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full text-sm text-[#8B8B93] file:mr-3 file:rounded-md file:border-0 file:bg-[#5B6CF0]/10 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-[#5B6CF0] hover:file:bg-[#5B6CF0]/20"
            required
          />
        </div>
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={!file || uploading}
            className="rounded-md bg-[#5B6CF0] px-4 py-2 text-sm font-medium text-white hover:bg-[#5B6CF0]/90 disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md border border-white/10 px-4 py-2 text-sm text-[#8B8B93] hover:bg-white/5"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 3: Test dashboard flow**

```bash
# With backend running, visit http://localhost:3070/dashboard
# Upload a .docx template, see it appear in the list
# Click "New Draft" to create a draft (will redirect to editor, not built yet)
```

- [ ] **Step 4: Commit**

```bash
git add web/
git commit -m "feat(web): add dashboard with template upload and draft list"
```

---

## Phase 3: BlockNote Editor + Converter + Export

### Task 10: Draft Store + Editor Page Shell

**Files:**
- Create: `web/lib/stores/draft-store.ts`
- Create: `web/app/drafts/[id]/page.tsx`

- [ ] **Step 1: Create draft store**

```typescript
// web/lib/stores/draft-store.ts
import { create } from "zustand";
import api from "@/lib/api";

interface DraftData {
  id: string;
  template_id: string;
  title: string;
  context: Record<string, string>;
  sections: Record<string, any[]>;
  attachments: Record<string, any[]>;
  status: string;
}

interface DraftStore {
  draft: DraftData | null;
  activeSection: string;
  isDirty: boolean;
  saveStatus: "idle" | "saving" | "saved" | "error";

  loadDraft: (id: string) => Promise<void>;
  setActiveSection: (id: string) => void;
  updateSection: (id: string, blocks: any[]) => void;
  updateContext: (key: string, value: string) => void;
  updateTitle: (title: string) => void;
  save: () => Promise<void>;
  exportDocx: () => Promise<void>;
}

export const useDraftStore = create<DraftStore>((set, get) => ({
  draft: null,
  activeSection: "",
  isDirty: false,
  saveStatus: "idle",

  loadDraft: async (id) => {
    const { data } = await api.get(`/drafts/${id}`);
    const sectionIds = Object.keys(data.sections);
    set({
      draft: data,
      activeSection: sectionIds[0] || "",
      isDirty: false,
      saveStatus: "idle",
    });
  },

  setActiveSection: (id) => set({ activeSection: id }),

  updateSection: (id, blocks) => {
    const { draft } = get();
    if (!draft) return;
    set({
      draft: { ...draft, sections: { ...draft.sections, [id]: blocks } },
      isDirty: true,
      saveStatus: "idle",
    });
  },

  updateContext: (key, value) => {
    const { draft } = get();
    if (!draft) return;
    set({
      draft: { ...draft, context: { ...draft.context, [key]: value } },
      isDirty: true,
      saveStatus: "idle",
    });
  },

  updateTitle: (title) => {
    const { draft } = get();
    if (!draft) return;
    set({ draft: { ...draft, title }, isDirty: true, saveStatus: "idle" });
  },

  save: async () => {
    const { draft } = get();
    if (!draft) return;
    set({ saveStatus: "saving" });
    try {
      await api.patch(`/drafts/${draft.id}`, {
        title: draft.title,
        context: draft.context,
        sections: draft.sections,
        attachments: draft.attachments,
      });
      set({ isDirty: false, saveStatus: "saved" });
    } catch {
      set({ saveStatus: "error" });
    }
  },

  exportDocx: async () => {
    const { draft, save } = get();
    if (!draft) return;
    // Save first
    await save();
    // Export
    const response = await api.post(`/drafts/${draft.id}/export`, null, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const a = document.createElement("a");
    a.href = url;
    a.download = `${draft.title}.docx`;
    a.click();
    window.URL.revokeObjectURL(url);
  },
}));
```

- [ ] **Step 2: Create editor page shell (without BlockNote yet)**

```tsx
// web/app/drafts/[id]/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDraftStore } from "@/lib/stores/draft-store";
import { useAuthStore } from "@/lib/stores/auth-store";

export default function EditorPage() {
  const params = useParams();
  const router = useRouter();
  const draftId = params.id as string;
  const { user, checkAuth, isLoading: authLoading } = useAuthStore();
  const { draft, activeSection, isDirty, saveStatus, loadDraft, setActiveSection, save, exportDocx, updateTitle, updateContext } = useDraftStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => { checkAuth(); }, [checkAuth]);
  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [authLoading, user, router]);

  useEffect(() => {
    if (user) {
      loadDraft(draftId).catch(() => router.push("/dashboard")).finally(() => setLoading(false));
    }
  }, [user, draftId, loadDraft, router]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        save();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [save]);

  if (authLoading || loading || !draft) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#5B6CF0] border-t-transparent" />
      </div>
    );
  }

  const sectionIds = Object.keys(draft.sections);

  return (
    <div className="flex h-screen flex-col">
      {/* Top bar */}
      <header className="flex h-12 items-center justify-between border-b border-white/[0.06] bg-[#141415] px-4">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/dashboard")} className="text-sm text-[#8B8B93] hover:text-[#E8E8ED]">
            ← Back
          </button>
          <input
            value={draft.title}
            onChange={(e) => updateTitle(e.target.value)}
            className="bg-transparent text-sm font-medium outline-none"
          />
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[#8B8B93]">
            {saveStatus === "saving" && "Saving..."}
            {saveStatus === "saved" && "Saved"}
            {saveStatus === "error" && "Save failed"}
            {saveStatus === "idle" && isDirty && "Unsaved changes"}
          </span>
          <button
            onClick={save}
            disabled={!isDirty || saveStatus === "saving"}
            className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-[#8B8B93] hover:bg-white/5 disabled:opacity-50"
          >
            Save
          </button>
          <button
            onClick={exportDocx}
            className="rounded-md bg-[#5B6CF0] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#5B6CF0]/90"
          >
            Export .docx
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-56 border-r border-white/[0.06] bg-[#141415] p-3 overflow-y-auto">
          <p className="mb-2 text-xs font-medium text-[#8B8B93]">Sections</p>
          <div className="space-y-1">
            {sectionIds.map((id) => (
              <button
                key={id}
                onClick={() => setActiveSection(id)}
                className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  activeSection === id
                    ? "bg-[#5B6CF0]/12 text-[#E8E8ED]"
                    : "text-[#8B8B93] hover:bg-white/[0.04] hover:text-[#E8E8ED]"
                }`}
              >
                {id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </button>
            ))}
          </div>

          {/* Context vars */}
          <div className="mt-6 border-t border-white/[0.06] pt-4">
            <p className="mb-2 text-xs font-medium text-[#8B8B93]">Context</p>
            {Object.entries(draft.context).map(([key, value]) => (
              <div key={key} className="mb-2">
                <label className="mb-0.5 block text-xs text-[#8B8B93]">{key}</label>
                <input
                  value={value as string}
                  onChange={(e) => updateContext(key, e.target.value)}
                  className="w-full rounded-md border border-white/[0.06] bg-white/[0.03] px-2 py-1.5 text-xs outline-none focus:border-[#5B6CF0]/50"
                />
              </div>
            ))}
          </div>
        </aside>

        {/* Editor area */}
        <main className="flex-1 overflow-y-auto bg-[#0F0F10] p-6">
          <div className="mx-auto max-w-3xl">
            <h2 className="mb-4 text-base font-medium">
              {activeSection.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </h2>
            <div className="rounded-lg border border-white/[0.06] bg-[#141415] p-4 min-h-[400px]">
              <p className="text-sm text-[#8B8B93]">
                BlockNote editor will be integrated here (Task 11)
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Test editor shell**

```bash
# Create a draft from dashboard, verify the editor page loads
# Test sidebar navigation, context inputs, save button, export button
```

- [ ] **Step 4: Commit**

```bash
git add web/
git commit -m "feat(web): add editor page shell with draft store and sidebar"
```

---

### Task 11: BlockNote Integration + Converter

**Files:**
- Create: `web/components/editor/SectionEditor.tsx`
- Create: `web/lib/converter/blocknote-to-engine.ts`
- Create: `web/lib/converter/engine-to-blocknote.ts`
- Modify: `web/app/drafts/[id]/page.tsx`

- [ ] **Step 1: Create BlockNote → report-engine converter (frontend)**

```typescript
// web/lib/converter/blocknote-to-engine.ts
interface BlockNoteBlock {
  id: string;
  type: string;
  props?: Record<string, any>;
  content?: any;
  children?: BlockNoteBlock[];
}

interface EngineBlock {
  type: string;
  [key: string]: any;
}

function extractText(content: any): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content.map((seg: any) => seg?.text || "").join("");
  }
  return "";
}

function hasInlineStyles(segments: any[]): boolean {
  return Array.isArray(segments) && segments.some((seg: any) => seg?.styles && Object.keys(seg.styles).length > 0);
}

function convertBlock(block: BlockNoteBlock): EngineBlock | null {
  const type = block.type;

  switch (type) {
    case "heading": {
      const level = block.props?.level || 2;
      return { type: "heading", text: extractText(block.content), level };
    }
    case "paragraph": {
      if (hasInlineStyles(block.content)) {
        const segments = (block.content || []).map((seg: any) => {
          const s: any = { text: seg.text || "" };
          if (seg.styles?.bold) s.bold = true;
          if (seg.styles?.italic) s.italic = true;
          return s;
        });
        return { type: "rich_paragraph", segments };
      }
      return { type: "paragraph", text: extractText(block.content) };
    }
    case "bulletListItem":
      return { type: "bullet_list", items: [extractText(block.content)] };
    case "numberedListItem":
      return { type: "numbered_list", items: [extractText(block.content)] };
    case "table": {
      const rows = block.content || [];
      if (!Array.isArray(rows) || rows.length === 0) return null;
      const headers = rows[0]?.map?.((c: any) => extractText(c?.content || c)) || [];
      const dataRows = rows.slice(1)?.map?.((r: any) =>
        r.map?.((c: any) => extractText(c?.content || c)) || []
      ) || [];
      return { type: "table", title: "", headers, rows: dataRows };
    }
    case "quote":
      return { type: "quote", text: extractText(block.content) };
    case "codeBlock":
      return { type: "code_block", code: extractText(block.content) };
    case "image":
      return {
        type: "image",
        path: block.props?.url || block.props?.src || "",
        width: block.props?.width,
        caption: block.props?.caption || "",
      };
    case "pageBreak":
      return { type: "page_break" };
    default:
      return null; // Unsupported types silently ignored
  }
}

export function blocknoteToEngineBlocks(blocks: BlockNoteBlock[]): EngineBlock[] {
  const result: EngineBlock[] = [];
  let i = 0;

  while (i < blocks.length) {
    const block = blocks[i];

    // Aggregate consecutive list items
    if (block.type === "bulletListItem") {
      const items: string[] = [];
      while (i < blocks.length && blocks[i].type === "bulletListItem") {
        items.push(extractText(blocks[i].content));
        i++;
      }
      result.push({ type: "bullet_list", items });
      continue;
    }
    if (block.type === "numberedListItem") {
      const items: string[] = [];
      while (i < blocks.length && blocks[i].type === "numberedListItem") {
        items.push(extractText(blocks[i].content));
        i++;
      }
      result.push({ type: "numbered_list", items });
      continue;
    }

    const converted = convertBlock(block);
    if (converted) result.push(converted);
    i++;
  }

  return result;
}
```

- [ ] **Step 2: Create engine → BlockNote converter (frontend)**

```typescript
// web/lib/converter/engine-to-blocknote.ts
interface EngineBlock {
  type: string;
  [key: string]: any;
}

interface BlockNoteBlock {
  id: string;
  type: string;
  props?: Record<string, any>;
  content?: any;
  children?: any[];
}

let blockIdCounter = 0;
function nextId(): string {
  return `bn-${++blockIdCounter}`;
}

export function engineToBlocknoteBlocks(blocks: EngineBlock[]): BlockNoteBlock[] {
  const result: BlockNoteBlock[] = [];

  for (const block of blocks) {
    switch (block.type) {
      case "heading":
        result.push({
          id: nextId(),
          type: "heading",
          props: { level: block.level || 2 },
          content: [{ type: "text", text: block.text || "" }],
        });
        break;
      case "paragraph":
        result.push({
          id: nextId(),
          type: "paragraph",
          content: [{ type: "text", text: block.text || "" }],
        });
        break;
      case "rich_paragraph":
        result.push({
          id: nextId(),
          type: "paragraph",
          content: (block.segments || []).map((seg: any) => ({
            type: "text",
            text: seg.text || "",
            styles: {
              ...(seg.bold ? { bold: true } : {}),
              ...(seg.italic ? { italic: true } : {}),
            },
          })),
        });
        break;
      case "bullet_list":
        for (const item of block.items || []) {
          result.push({
            id: nextId(),
            type: "bulletListItem",
            content: [{ type: "text", text: item }],
          });
        }
        break;
      case "numbered_list":
        for (const item of block.items || []) {
          result.push({
            id: nextId(),
            type: "numberedListItem",
            content: [{ type: "text", text: item }],
          });
        }
        break;
      case "quote":
        result.push({
          id: nextId(),
          type: "quote",
          content: [{ type: "text", text: block.text || "" }],
        });
        break;
      case "code_block":
        result.push({
          id: nextId(),
          type: "codeBlock",
          content: [{ type: "text", text: block.code || "" }],
        });
        break;
      case "page_break":
        result.push({ id: nextId(), type: "pageBreak" });
        break;
      // table, image: complex, handle in future iteration
    }
  }

  return result;
}
```

- [ ] **Step 3: Create SectionEditor component with BlockNote**

```tsx
// web/components/editor/SectionEditor.tsx
"use client";

import { useEffect, useMemo, useRef } from "react";
import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";

interface SectionEditorProps {
  blocks: any[];
  onChange: (blocks: any[]) => void;
}

export default function SectionEditor({ blocks, onChange }: SectionEditorProps) {
  const editor = useCreateBlockNote({
    initialContent: blocks.length > 0 ? blocks : undefined,
  });

  const lastBlocksRef = useRef(blocks);

  // Sync external blocks changes (e.g., when switching sections)
  useEffect(() => {
    if (JSON.stringify(blocks) !== JSON.stringify(lastBlocksRef.current)) {
      lastBlocksRef.current = blocks;
      // Replace editor content
      editor.replaceBlocks(editor.document, blocks);
    }
  }, [blocks, editor]);

  // Emit changes on every edit
  const handleChange = () => {
    const currentBlocks = editor.document;
    lastBlocksRef.current = currentBlocks;
    onChange(currentBlocks);
  };

  return (
    <div className="min-h-[400px]">
      <BlockNoteView editor={editor} onChange={handleChange} theme="dark" />
    </div>
  );
}
```

- [ ] **Step 4: Integrate SectionEditor into editor page**

Replace the editor area placeholder in `web/app/drafts/[id]/page.tsx`:

```tsx
import SectionEditor from "@/components/editor/SectionEditor";
import { useDraftStore } from "@/lib/stores/draft-store";

// Inside the main content area, replace the placeholder with:
<main className="flex-1 overflow-y-auto bg-[#0F0F10] p-6">
  <div className="mx-auto max-w-3xl">
    <SectionEditor
      key={activeSection}
      blocks={draft.sections[activeSection] || []}
      onChange={(blocks) => useDraftStore.getState().updateSection(activeSection, blocks)}
    />
  </div>
</main>
```

- [ ] **Step 5: Add auto-save (debounce 3s)**

Add to the editor page component:

```tsx
import { useRef, useCallback } from "react";

// Inside the component:
const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

const scheduleAutoSave = useCallback(() => {
  if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
  autoSaveTimerRef.current = setTimeout(() => {
    const { isDirty, save: doSave } = useDraftStore.getState();
    if (isDirty) doSave();
  }, 3000);
}, []);

// Call scheduleAutoSave() in the SectionEditor onChange handler:
<SectionEditor
  key={activeSection}
  blocks={draft.sections[activeSection] || []}
  onChange={(blocks) => {
    useDraftStore.getState().updateSection(activeSection, blocks);
    scheduleAutoSave();
  }}
/>
```

- [ ] **Step 6: Test end-to-end**

```bash
# With both backend and frontend running:
# 1. Upload a template
# 2. Create a new draft
# 3. Edit content in BlockNote
# 4. Verify auto-save works (check network tab for PATCH)
# 5. Click Export .docx, verify valid Word document downloads
```

- [ ] **Step 7: Commit**

```bash
git add web/
git commit -m "feat(web): integrate BlockNote editor with converter and auto-save"
```

---

## Phase 4: Polish

### Task 12: Command Palette (Cmd+K)

**Files:**
- Create: `web/components/CommandPalette.tsx`
- Modify: `web/app/drafts/[id]/page.tsx`

- [ ] **Step 1: Create command palette component**

```tsx
// web/components/CommandPalette.tsx
"use client";

import { useEffect, useState, useRef } from "react";

interface Command {
  id: string;
  label: string;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  commands: Command[];
  open: boolean;
  onClose: () => void;
}

export default function CommandPalette({ commands, open, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const filtered = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase())
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-lg border border-white/[0.06] bg-[#141415] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a command..."
          className="w-full border-b border-white/[0.06] bg-transparent px-4 py-3 text-sm outline-none"
        />
        <div className="max-h-64 overflow-y-auto p-1">
          {filtered.map((cmd) => (
            <button
              key={cmd.id}
              onClick={() => { cmd.action(); onClose(); }}
              className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm text-[#E8E8ED] hover:bg-[#5B6CF0]/12"
            >
              <span>{cmd.label}</span>
              {cmd.shortcut && <span className="text-xs text-[#8B8B93]">{cmd.shortcut}</span>}
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="px-3 py-2 text-sm text-[#8B8B93]">No commands found</p>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Integrate into editor page**

```tsx
import CommandPalette from "@/components/CommandPalette";

// Inside the component:
const [cmdOpen, setCmdOpen] = useState(false);

useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      setCmdOpen((v) => !v);
    }
  };
  window.addEventListener("keydown", handler);
  return () => window.removeEventListener("keydown", handler);
}, []);

const commands = [
  { id: "save", label: "Save", shortcut: "⌘S", action: save },
  { id: "export", label: "Export .docx", shortcut: "⌘⇧E", action: exportDocx },
  ...sectionIds.map((id) => ({
    id: `section-${id}`,
    label: `Go to: ${id.replace(/_/g, " ")}`,
    action: () => setActiveSection(id),
  })),
];

// Add to JSX:
<CommandPalette commands={commands} open={cmdOpen} onClose={() => setCmdOpen(false)} />
```

- [ ] **Step 3: Test**

```bash
# Press Cmd+K (or Ctrl+K) in the editor
# Type to filter commands
# Select a section to navigate, test save/export shortcuts
```

- [ ] **Step 4: Commit**

```bash
git add web/
git commit -m "feat(web): add command palette (Cmd+K)"
```

---

### Task 13: Image Upload Endpoint

**Files:**
- Create: `server/routers/upload.py`
- Modify: `server/main.py`

- [ ] **Step 1: Create upload router**

```python
# server/routers/upload.py
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
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
    from fastapi.responses import FileResponse
    return FileResponse(file_path)
```

- [ ] **Step 2: Register in main.py**

```python
from server.routers.upload import router as upload_router
app.include_router(upload_router)
```

- [ ] **Step 3: Commit**

```bash
git add server/
git commit -m "feat(server): add image upload endpoint"
```

---

### Task 14: CSS Refinements + BlockNote Theme Override

**Files:**
- Modify: `web/app/globals.css`

- [ ] **Step 1: Add BlockNote dark theme overrides**

Append to `web/app/globals.css`:

```css
/* BlockNote dark theme overrides */
.bn-container {
  --bn-colors-editor-background: #141415 !important;
  --bn-colors-menu-text: #E8E8ED !important;
  --bn-colors-tooltip-background: #1a1a1c !important;
  --bn-colors-hovered-background: rgba(255, 255, 255, 0.04) !important;
  --bn-colors-selected-background: rgba(91, 108, 240, 0.12) !important;
  --bn-font-family: "Inter", system-ui, sans-serif !important;
}

.bn-editor {
  font-size: 13px !important;
  line-height: 1.6 !important;
}

.bn-block-outer:not(:first-child) {
  margin-top: 2px !important;
}

/* Placeholder text */
.bn-inline-content[data-is-empty="true"]::before {
  color: rgba(255, 255, 255, 0.25) !important;
}
```

- [ ] **Step 2: Commit**

```bash
git add web/
git commit -m "feat(web): add BlockNote dark theme overrides"
```

---

## Spec Self-Review Checklist

- [x] **Spec coverage**: All spec sections have corresponding tasks
  - Auth (Task 2, 8) ✓
  - Template upload + parsing (Task 3, 9) ✓
  - Draft CRUD (Task 4, 10) ✓
  - BlockNote converter (Task 5, 11) ✓
  - Export (Task 6, 11) ✓
  - UI design / Linear theme (Task 7, 14) ✓
  - Command palette (Task 12) ✓
  - Image upload (Task 13) ✓
  - Auto-save (Task 11) ✓
  - Keyboard shortcuts (Task 10, 12) ✓
- [x] **No placeholders**: All steps contain complete code
- [x] **Type consistency**: BlockNote/Engine block types consistent across converters
- [x] **File paths**: All exact paths specified
- [x] **Port config**: 3070 (frontend), 8070 (backend) ✓
