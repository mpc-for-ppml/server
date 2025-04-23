from fastapi import APIRouter

from app.api.routes import upload, ws, sessions

api_router = APIRouter()
api_router.include_router(sessions.router)
api_router.include_router(upload.router)
api_router.include_router(ws.router)
