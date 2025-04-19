from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.services.file_service import save_user_csv

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/")
async def upload_csv(
    group_id: str = Form(...),
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed."
        )

    try:
        save_user_csv(group_id, user_id, file)
    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already uploaded a file to this group."
        )

    return {"message": "File uploaded successfully"}
