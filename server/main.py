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
