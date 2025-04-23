from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    participant_count: int
    lead_user_id: str

# In-memory store for demo; swap out for a real DB
_sessions: dict[str, dict] = {}

@router.post("/", status_code=201)
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    _sessions[sid] = {
        "lead": body.lead_user_id,
        "participant_count": body.participant_count,
        "joined": set(),         # track user_ids who have connected
        "status_map": {},        # user_id → bool
    }
    return {"session_id": sid}

@router.get("/{session_id}")
def get_session(session_id: str):
    s = _sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "participant_count": s["participant_count"],
        "joined_count": len(s["joined"]),
    }

