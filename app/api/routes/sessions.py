from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
from utils.data_loader import ensure_log_file_exists
from utils.constant import LOG_DIR
from .state import _sessions
import uuid
import os
import sys
import subprocess
import time

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
        "status_map": {}        # user_id → bool
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

@router.post("/{session_id}/run")
async def proceed(session_id: str, background_tasks: BackgroundTasks, request: Request):
    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    # Parsing the data
    data = await request.json()
    user_id = data.get("userId", "")
    normalizer = data.get("normalizer", "zscore")
    regression = data.get("regression", "linear")
    lr = str(data.get("learningRate", 0.5))
    epochs = str(data.get("epochs", 1000))
    is_logging = data.get("isLogging", False)

    # Only allow lead to trigger
    if user_id != sess["lead"]:
        raise HTTPException(403, "Only lead can initiate the run")

    ensure_log_file_exists()
    
    def run_and_log():
        session_dir = os.path.join("uploads", session_id)
        if not os.path.exists(session_dir):
            raise RuntimeError(f"Session upload folder {session_dir} does not exist")

        # Collect all user CSVs in session folder
        user_files = sorted([
            f for f in os.listdir(session_dir) 
            if f.endswith(".csv")
        ])

        # Assign party ids: lead always gets -I0, others get -I1, -I2, ...
        user_file_map = {}
        party_id = 0
        for fname in user_files:
            uid = fname.replace(".csv", "")
            if uid == user_id:
                user_file_map[uid] = 0  # lead is always party 0
            else:
                party_id += 1
                user_file_map[uid] = party_id

        num_parties = len(user_file_map)
        processes = []

        os.makedirs(LOG_DIR, exist_ok=True)  # Ensure logs/ exists

        for uid, pid in user_file_map.items():
            csv_path = os.path.join(session_dir, f"{uid}.csv")
            party_log_path = os.path.join(LOG_DIR, f"log_{pid}.log")

            # Clear log
            with open(party_log_path, "w", encoding="utf-8") as f:
                f.write("")

            logfile = open(party_log_path, "a", encoding="utf-8")

            cmd = [
                sys.executable, "-u", "mpyc_task.py",
                "-M", str(num_parties),
                "-I", str(pid),
                csv_path,
                "-n", normalizer,
                "-r", regression,
                "--lr", lr,
                "--epochs", epochs
            ]

            if is_logging:
                cmd.append("--verbose")

            p = subprocess.Popen(
                cmd,
                stdout=logfile,
                stderr=logfile,
                bufsize=1,
                universal_newlines=True,
            )
            processes.append((p, logfile))
            time.sleep(0.1)  # slight delay to reduce contention

        for p, logfile in processes:
            p.wait()
            logfile.close()

    background_tasks.add_task(run_and_log)
    return {"status": "started", "initiated_by": user_id}
