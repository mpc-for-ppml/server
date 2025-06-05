from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from utils.constant import LOG_DIR, UPLOAD_DIR, MODEL_DIR
from .state import _sessions
from services.file_service import ensure_log_file_exists
from services.result_service import ResultService
from services.prediction_service import PredictionService
from interface.session_state import SessionState, SessionStateInfo, StateCheckRequest, StateCheckResponse
from interface.identifier_config import IdentifierConfig, IdentifierMode
from datetime import datetime
from typing import List, Dict
import uuid
import json
import os
import sys
import subprocess
import time
import pickle
import pandas as pd
import io

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
    identifierConfig: IdentifierConfig  # Now required

class PredictRequest(BaseModel):
    data: List[Dict[str, float]]

class PredictResponse(BaseModel):
    predictions: List[float]

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

@router.get("/{session_id}/common-columns")
def get_common_columns(session_id: str):
    """
    Analyze all uploaded CSV files in the session and return common columns
    that could be used as identifiers
    """
    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if all users have uploaded
    if len(sess.uploaded_users) < sess.participant_count:
        raise HTTPException(
            status_code=400, 
            detail=f"Not all users have uploaded. {len(sess.uploaded_users)}/{sess.participant_count} uploaded"
        )
    
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session upload folder not found")
    
    # Analyze all CSV files
    all_columns = {}
    user_columns = {}
    
    for user_id in sess.uploaded_users:
        csv_path = os.path.join(session_dir, f"{user_id}.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            columns = set(df.columns.tolist())
            user_columns[user_id] = columns
            
            # Track column info
            for col in columns:
                if col not in all_columns:
                    all_columns[col] = {
                        "name": col,
                        "present_in_users": [],
                        "unique_counts": {},
                        "dtypes": {},
                        "sample_values": []
                    }
                
                all_columns[col]["present_in_users"].append(user_id)
                all_columns[col]["unique_counts"][user_id] = df[col].nunique()
                all_columns[col]["dtypes"][user_id] = str(df[col].dtype)
                
                # Add sample values from first user only
                if len(all_columns[col]["sample_values"]) == 0:
                    all_columns[col]["sample_values"] = df[col].dropna().head(3).tolist()
    
    # Find common columns (present in all users)
    common_columns = []
    for col_name, col_info in all_columns.items():
        if len(col_info["present_in_users"]) == sess.participant_count:
            # Check if it could be a good identifier
            is_good_identifier = all(
                col_info["unique_counts"][user] > 1 
                for user in col_info["present_in_users"]
            )
            
            common_columns.append({
                "name": col_name,
                "is_potential_identifier": is_good_identifier,
                "unique_counts": col_info["unique_counts"],
                "dtypes": col_info["dtypes"],
                "sample_values": col_info["sample_values"]
            })
    
    # Check if there are NO common columns
    if not common_columns:
        # Provide detailed information about what each party has
        return {
            "session_id": session_id,
            "total_users": sess.participant_count,
            "common_columns": [],
            "potential_labels": [],
            "all_columns_by_user": {user: list(cols) for user, cols in user_columns.items()},
            "error": "No common columns found across all parties",
            "recommendation": "All parties must have at least one column with the same name to proceed with MPC"
        }
    
    # Identify label columns (columns that might be labels)
    potential_labels = []
    label_candidates = ["will_purchase", "purchase_amount", "label", "target", "y"]
    
    for col in common_columns:
        if col["name"].lower() in label_candidates:
            potential_labels.append(col["name"])
    
    return {
        "session_id": session_id,
        "total_users": sess.participant_count,
        "common_columns": common_columns,
        "potential_labels": potential_labels,
        "all_columns_by_user": {user: list(cols) for user, cols in user_columns.items()}
    }

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
    identifier_config = body.identifierConfig

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
    
    # Validate identifier columns exist in all uploaded files
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(400, "Session upload folder not found")
    
    # First check if there are any common columns at all
    all_columns_sets = []
    for user_id in sess.uploaded_users:
        csv_path = os.path.join(session_dir, f"{user_id}.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, nrows=1)  # Just read header
            all_columns_sets.append(set(df.columns))
    
    # Find intersection of all column sets
    common_cols = set.intersection(*all_columns_sets) if all_columns_sets else set()
    
    if not common_cols:
        raise HTTPException(
            400,
            "Cannot proceed: No common columns found across all parties. "
            "All parties must have at least one column with the same name."
        )
    
    # Check each uploaded file has the required identifier columns
    for user_id in sess.uploaded_users:
        csv_path = os.path.join(session_dir, f"{user_id}.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, nrows=1)  # Just read header
            missing_cols = [col for col in identifier_config.columns if col not in df.columns]
            if missing_cols:
                raise HTTPException(
                    400, 
                    f"User {user_id}'s file is missing identifier columns: {missing_cols}"
                )
    
    # Update state to PROCESSING
    sess.state = SessionState.PROCESSING
    sess.processing_started_at = datetime.now()
    sess.updated_at = datetime.now()

    ensure_log_file_exists(session_id)
    
    def run_and_log():
        session_dir = os.path.join(UPLOAD_DIR, session_id)
        if not os.path.exists(session_dir):
            raise RuntimeError(f"Session upload folder {session_dir} does not exist")
        
        ensure_log_file_exists(session_id)

        # Collect all user CSVs in session folder
        user_files = sorted([
            f for f in os.listdir(session_dir) 
            if f.endswith(".csv")
        ])

        # Assign party ids: find which user has the label column and make them party 0
        user_file_map = {}
        label_owner = None
        
        # Find which user has the label column
        for fname in user_files:
            uid = fname.replace(".csv", "")
            csv_path = os.path.join(session_dir, fname)
            df = pd.read_csv(csv_path, nrows=1)  # Just read header
            if label in df.columns:
                label_owner = uid
                break
        
        # Assign party IDs with label owner as party 0
        if label_owner:
            user_file_map[label_owner] = 0  # Party with label becomes party 0
            party_id = 1
            for fname in user_files:
                uid = fname.replace(".csv", "")
                if uid != label_owner:
                    user_file_map[uid] = party_id
                    party_id += 1
        else:
            # Fallback: lead is party 0 (original behavior)
            party_id = 0
            for fname in user_files:
                uid = fname.replace(".csv", "")
                if uid == user_id:
                    user_file_map[uid] = 0  # lead is always party 0
                else:
                    party_id += 1
                    user_file_map[uid] = party_id

        # Log party assignments for debugging
        print(f"🎭 Party assignments for label '{label}':")
        for uid, pid in user_file_map.items():
            csv_path = os.path.join(session_dir, f"{uid}.csv")
            df = pd.read_csv(csv_path, nrows=1)
            has_label = label in df.columns
            print(f"   Party {pid}: {uid} {'(HAS LABEL)' if has_label else ''}")

        num_parties = len(user_file_map)
        processes = []

        for uid, pid in user_file_map.items():
            csv_path = os.path.join(session_dir, f"{uid}.csv")
            party_log_path = os.path.join(LOG_DIR, session_id, f"log_{uid}.log")

            # Clear log
            with open(party_log_path, "w", encoding="utf-8") as f:
                f.write("")

            logfile = open(party_log_path, "a", encoding="utf-8")

            cmd = [
                sys.executable, "-u", "app/mpyc_task.py",
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
            
            # Add identifier config if it's not the default
            if identifier_config and (identifier_config.mode != IdentifierMode.SINGLE or 
                                    identifier_config.columns != ["user_id"]):
                config_json = json.dumps(identifier_config.dict())
                cmd.extend(["--identifier-config", config_json])

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
    model_path = os.path.join(MODEL_DIR, result.summary.modelPath)
    
    # Check if the file exists
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model file not found")
    
    # Return the file
    return FileResponse(
        path=model_path,
        filename=result.summary.modelPath,
        media_type="application/octet-stream"
    )

@router.post("/{session_id}/predict", response_model=PredictResponse)
def predict(session_id: str, body: PredictRequest):
    """Make predictions using the trained model for single or multiple data points"""
    # Check if session exists
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if results exist
    result = ResultService.get_result(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Model not available yet")
    
    # Check if model path exists
    if not result.summary.modelPath:
        raise HTTPException(status_code=404, detail="Model file not available")
    
    # Construct model path
    model_path = os.path.join(MODEL_DIR, result.summary.modelPath)
    
    try:
        # Validate that all required features are present in each data point
        with open(model_path, "rb") as f:
            model_data = pickle.load(f)
        
        feature_names = model_data["feature_names"]
        for data_point in body.data:
            for feature in feature_names:
                if feature not in data_point:
                    raise ValueError(f"Missing required feature: {feature}")
        
        # Use PredictionService to make predictions
        predictions = PredictionService.load_model_and_predict(model_path, body.data)
        
        # Round predictions for consistency
        predictions = [round(p, 4) for p in predictions]
        
        return PredictResponse(predictions=predictions)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model file not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/{session_id}/predict-batch", response_model=PredictResponse)
async def predict_batch(session_id: str, file: UploadFile = File(...)):
    """Make batch predictions using the trained model from a CSV file"""
    # Check if session exists
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if results exist
    result = ResultService.get_result(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Model not available yet")
    
    # Check if model path exists
    if not result.summary.modelPath:
        raise HTTPException(status_code=404, detail="Model file not available")
    
    # Construct model path
    model_path = os.path.join(MODEL_DIR, result.summary.modelPath)
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Load model to get feature names for validation
        with open(model_path, "rb") as f:
            model_data = pickle.load(f)
        
        feature_names = model_data["feature_names"]
        
        # Validate that all required features are present
        for feature in feature_names:
            if feature not in df.columns:
                raise ValueError(f"Missing required feature in CSV: {feature}")
        
        # Convert DataFrame to list of dictionaries for PredictionService
        data_points = []
        for _, row in df.iterrows():
            data_point = {feature: float(row[feature]) for feature in feature_names}
            data_points.append(data_point)
        
        # Use PredictionService to make predictions
        predictions = PredictionService.load_model_and_predict(model_path, data_points)
        
        # Round predictions for consistency
        predictions = [round(p, 4) for p in predictions]
        
        return PredictResponse(predictions=predictions)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model file not found")
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
