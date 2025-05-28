from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import json
from fastapi import BackgroundTasks
import shlex, asyncio
from subprocess import run, PIPE
from .state import _sessions, active_connections

router = APIRouter(prefix="/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    participant_count: int
    lead_user_id: str

@router.post("/", status_code=201)
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    _sessions[sid] = {
        "lead": body.lead_user_id,
        "participant_count": body.participant_count,
        "joined": set(),         # track user_ids who have connected
        "status_map": {},        # user_id → bool
        "party_map": {},         # user_id → party_id (1-based)
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

@router.get("/{session_id}/party/{user_id}")
def get_party_id(session_id: str, user_id: str):
    session = _sessions.get(session_id)
    if not session or user_id not in session["party_map"]:
        raise HTTPException(404, "User not found in session")
    return {"party_id": session["party_map"][user_id]}

@router.post("/{session_id}/proceed")
async def proceed(session_id: str, background_tasks: BackgroundTasks):
    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    print("Current status map:", sess["status_map"])
    print("Expected participants:", sess["participant_count"])
    if len(sess["status_map"]) != sess["participant_count"] or not all(sess["status_map"].values()):
        raise HTTPException(400, "Not all users are ready")

    async def run_mpc_for_user(user_id: str):
        party_id = sess["party_map"][user_id]
        data_path = f"data/{session_id}/{user_id}.csv"
        command = f"python secure_logreg.py -M{sess['participant_count']} -I{party_id} {data_path} -n zscore"
        result = run(shlex.split(command), stdout=PIPE, stderr=PIPE, text=True)

        # Kirim hasil ke semua klien di sesi
        message = json.dumps({
            "event": "mpc_result",
            "user_id": user_id,
            "stdout": result.stdout,
            "stderr": result.stderr,
        })

        for conn in active_connections.get(session_id, []):
            await conn.send_text(message)

    async def run_all():
        await asyncio.gather(*(run_mpc_for_user(uid) for uid in sess["joined"]))

    # Jalankan di background
    background_tasks.add_task(run_all)
    return {"message": "MPC started"}
