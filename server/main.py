from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import ensure_dirs
from server.database import init_db
from server.routers.auth import router as auth_router
from server.routers.templates import router as templates_router
from server.routers.drafts import router as drafts_router
from server.routers.upload import router as upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    init_db()
    yield


app = FastAPI(title="Report Editor API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3070"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(templates_router)
app.include_router(drafts_router)
app.include_router(upload_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
