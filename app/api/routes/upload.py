from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from services.file_service import save_user_csv
from .ws import active_connections
from .state import _sessions
from interface.session_state import SessionState
from datetime import datetime
import json

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/")
async def upload_csv(
    group_id: str = Form(...),
    user_id:  str = Form(...),
    org_name: str | None = Form(None),
    label:    str | None = Form(None),
    file:     UploadFile = File(...),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed."
        )

    # Check if session exists
    sess = _sessions.get(group_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check if user is part of the session
    if user_id not in sess.joined_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not part of this session"
        )
    
    # Check session state
    if sess.state not in [SessionState.CREATED, SessionState.UPLOADING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload files in current session state: {sess.state}"
        )
    
    try:
        # on the lead path, enforce that org_name & label are present
        if sess.lead_user_id == user_id:
            if not org_name or not label:
                raise HTTPException(400, "Organization name & label required for lead")
        
        save_user_csv(group_id, user_id, file)
        
        # Track that this user has uploaded
        sess.uploaded_users.add(user_id)
        sess.updated_at = datetime.now()
        
        # Check if all users have uploaded
        if len(sess.uploaded_users) == sess.participant_count:
            sess.state = SessionState.READY
            sess.updated_at = datetime.now()

        # Notify all clients in the group
        if group_id in active_connections:
            message = json.dumps({
                "event": "file_uploaded",
                "user_id": user_id,
                "uploaded_count": len(sess.uploaded_users),
                "participant_count": sess.participant_count,
                "all_uploaded": len(sess.uploaded_users) == sess.participant_count,
                "session_state": sess.state
            })
            for connection in active_connections[group_id]:
                await connection.send_text(message)

    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already uploaded a file to this group."
        )

    return {"message": "File uploaded successfully"}
