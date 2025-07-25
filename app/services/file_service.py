import os
import shutil
from fastapi import UploadFile
from utils.constant import LOG_DIR, UPLOAD_DIR

def save_user_csv(group_id: str, user_id: str, file: UploadFile):
    group_path = os.path.join(UPLOAD_DIR, group_id)
    os.makedirs(group_path, exist_ok=True)

    file_path = os.path.join(group_path, f"{user_id}.csv")

    if os.path.exists(file_path):
        raise FileExistsError("File already exists for this user in the group.")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

def ensure_log_file_exists(session_id: str):
    session_log_dir = os.path.join(LOG_DIR, session_id)
    os.makedirs(session_log_dir, exist_ok=True)