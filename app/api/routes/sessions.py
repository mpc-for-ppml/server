from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from utils.data_loader import ensure_log_file_exists
from utils.constant import LOG_DIR, UPLOAD_DIR
from .state import _sessions
from services.result_service import ResultService
from interface.session_state import SessionState, SessionStateInfo, StateCheckRequest, StateCheckResponse
from datetime import datetime
import uuid
import os
import sys
import subprocess
import time

router = APIRouter(prefix="/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    participant_count: int
    lead_user_id: str

class RunConfig(BaseModel):
    userId: str
    normalizer: str = "zscore"
    regression: str = "linear"
    learningRate: float = 0.5
    epochs: int = 1000
    label: str
    isLogging: bool = False

@router.post("/", status_code=201)
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    now = datetime.now()
    _sessions[sid] = SessionStateInfo(
        state=SessionState.CREATED,
        session_id=sid,
        lead_user_id=body.lead_user_id,
        participant_count=body.participant_count,
        joined_users={body.lead_user_id},  # Automatically add lead user
        uploaded_users=set(),
        status_map={},
        has_results=False,
        created_at=now,
        updated_at=now
    )
    return {"session_id": sid}

@router.get("/{session_id}")
def get_session(session_id: str):
    s = _sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "participant_count": s.participant_count,
        "joined_count": len(s.joined_users),
    }

@router.post("/{session_id}/check-state")
def check_state(session_id: str, body: StateCheckRequest):
    """
    Check if a user can access a specific path based on session state.
    Used by frontend to validate navigation.
    """
    s = _sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if user can access the requested path
    allowed, reason = s.can_access_path(body.path, body.user_id)
    
    return StateCheckResponse(
        allowed=allowed,
        reason=reason,
        current_state=s.state,
        session_info={
            "session_id": s.session_id,
            "participant_count": s.participant_count,
            "joined_count": len(s.joined_users),
            "uploaded_count": len(s.uploaded_users),
            "is_lead": body.user_id == s.lead_user_id,
            "has_results": s.has_results
        }
    )

@router.post("/{session_id}/run")
async def proceed(session_id: str, background_tasks: BackgroundTasks, body: RunConfig):
    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    # Extract data from the request body
    user_id = body.userId
    normalizer = body.normalizer
    regression = body.regression
    lr = str(body.learningRate)
    epochs = str(body.epochs)
    label = body.label
    is_logging = body.isLogging

    # Only allow lead to trigger
    if user_id != sess.lead_user_id:
        raise HTTPException(403, "Only lead can initiate the run")
    
    # Check session state
    if sess.state != SessionState.READY:
        if sess.state == SessionState.UPLOADING:
            raise HTTPException(400, "Not all users have uploaded their files yet")
        elif sess.state == SessionState.PROCESSING:
            raise HTTPException(400, "Session is already processing")
        elif sess.state == SessionState.COMPLETED:
            raise HTTPException(400, "Session has already completed")
        else:
            raise HTTPException(400, f"Cannot start processing in current state: {sess.state}")
    
    # Update state to PROCESSING
    sess.state = SessionState.PROCESSING
    sess.processing_started_at = datetime.now()
    sess.updated_at = datetime.now()

    ensure_log_file_exists(session_id)
    
    def run_and_log():
        session_dir = os.path.join(UPLOAD_DIR, session_id)
        if not os.path.exists(session_dir):
            raise RuntimeError(f"Session upload folder {session_dir} does not exist")
        
        session_log_dir = os.path.join(LOG_DIR, session_id)
        os.makedirs(session_log_dir, exist_ok=True)

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
            party_log_path = os.path.join(session_log_dir, f"log_{pid}.log")

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
                "--epochs", epochs,
                "--label", label
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
        
        # Wait for all processes and check their return codes
        all_success = True
        error_messages = []
        for idx, (p, logfile) in enumerate(processes):
            return_code = p.wait()
            if return_code != 0:
                all_success = False
                error_messages.append(f"Process {idx} failed with return code {return_code}")
        
        # Update state based on results
        if all_success:
            sess.state = SessionState.COMPLETED
            sess.has_results = True
            sess.processing_completed_at = datetime.now()
        else:
            sess.state = SessionState.FAILED
            sess.error_message = "; ".join(error_messages)
        
        sess.updated_at = datetime.now()

    background_tasks.add_task(run_and_log)
    return {"status": "started", "initiated_by": user_id}

@router.get("/{session_id}/result")
def get_session_result(session_id: str):
    # Check if session exists
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get result using ResultService
    result = ResultService.get_result(session_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Results not available yet")
    
    # Convert to dict to add download link
    result_dict = result.model_dump()
    
    # Add model download link if model path exists
    if result.summary.modelPath:
        result_dict["modelDownloadUrl"] = f"/api/sessions/{session_id}/model/download"
    
    return result_dict

@router.get("/{session_id}/model/download")
def download_model(session_id: str):
    """Download the trained model pickle file for a session"""
    # Check if session exists
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if results exist
    result = ResultService.get_result(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Results not available yet")
    
    # Check if model path exists in results
    if not result.summary.modelPath:
        raise HTTPException(status_code=404, detail="Model file not available")
    
    # Construct the full path to the model file
    model_path = os.path.join("models", result.summary.modelPath)
    
    # Check if the file exists
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model file not found")
    
    # Return the file
    return FileResponse(
        path=model_path,
        filename=result.summary.modelPath,
        media_type="application/octet-stream"
    )
