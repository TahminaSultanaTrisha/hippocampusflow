"""App entry point. Run locally with:  uvicorn app.main:app --reload"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, memory, scans, users
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before launch
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(scans.router)
app.include_router(memory.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
