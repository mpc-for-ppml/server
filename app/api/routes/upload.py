from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from services.file_service import save_user_csv
from .ws import active_connections
from .sessions import _sessions
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

    try:
        # on the lead path, enforce that org_name & label are present
        if _sessions[group_id]["lead"] == user_id:
            if not org_name or not label:
                raise HTTPException(400, "Organization name & label required for lead")
        
        save_user_csv(group_id, user_id, file)

        # Notify all clients in the group
        if group_id in active_connections:
            message = json.dumps({
                "event": "file_uploaded",
                "user_id": user_id
            })
            for connection in active_connections[group_id]:
                await connection.send_text(message)

    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already uploaded a file to this group."
        )

    return {"message": "File uploaded successfully"}
