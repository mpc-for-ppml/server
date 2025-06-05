from fastapi import APIRouter

from api.routes import upload, ws, sessions, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(sessions.router)
api_router.include_router(upload.router)
api_router.include_router(ws.router)
