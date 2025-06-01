from enum import Enum
from typing import Dict, Set, Optional
from datetime import datetime
from pydantic import BaseModel


class SessionState(str, Enum):
    """Session workflow states"""
    CREATED = "created"  # Session created, waiting for uploads
    UPLOADING = "uploading"  # Users are uploading files
    READY = "ready"  # All files uploaded, ready to process
    PROCESSING = "processing"  # MPC computation in progress
    COMPLETED = "completed"  # Results available
    FAILED = "failed"  # Processing failed
    

class SessionStateInfo(BaseModel):
    """Detailed session state information"""
    state: SessionState
    session_id: str
    lead_user_id: str
    participant_count: int
    joined_users: Set[str] = set()
    uploaded_users: Set[str] = set()  # Track who has uploaded files
    status_map: Dict[str, bool] = {}  # User ready status
    has_results: bool = False
    created_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        use_enum_values = True
        
    def can_access_path(self, path: str, user_id: str) -> tuple[bool, str]:
        """
        Check if a user can access a specific path based on session state
        Returns: (allowed: bool, reason: str)
        """
        # Special case: Anyone can access form-upload in CREATED/UPLOADING state
        # This allows participants to join the session
        if path == "form-upload" and self.state in [SessionState.CREATED, SessionState.UPLOADING]:
            # Check if session is full (only for non-joined users)
            if user_id not in self.joined_users and len(self.joined_users) >= self.participant_count:
                return False, "Session is full"
            return True, "OK"
            
        # For other paths, check if user is part of the session
        if user_id not in self.joined_users:
            return False, "User is not part of this session"
            
        # Path access rules based on state
        if path == "form-upload":
            # Can access upload if session is in CREATED or UPLOADING state
            if self.state in [SessionState.CREATED, SessionState.UPLOADING]:
                return True, "OK"
            elif self.state == SessionState.READY:
                return False, "All files have been uploaded. Waiting for processing to start."
            elif self.state == SessionState.PROCESSING:
                return False, "Session is currently processing. Please go to the log page."
            elif self.state == SessionState.COMPLETED:
                return False, "Session has completed. Please go to the results page."
            else:
                return False, f"Cannot upload in current state: {self.state}"
                
        elif path == "log":
            # Can access log if processing has started
            if self.state == SessionState.PROCESSING:
                return True, "OK"
            elif self.state in [SessionState.CREATED, SessionState.UPLOADING, SessionState.READY]:
                return False, "Processing has not started yet. Please complete the upload first."
            elif self.state == SessionState.COMPLETED:
                return True, "OK"  # Can still view logs after completion
            else:
                return False, f"Cannot view logs in current state: {self.state}"
                
        elif path == "result":
            # Can only access results if completed
            if self.state == SessionState.COMPLETED:
                return True, "OK"
            elif self.state == SessionState.PROCESSING:
                return False, "Processing is still in progress. Please wait for completion."
            elif self.state in [SessionState.CREATED, SessionState.UPLOADING, SessionState.READY]:
                return False, "Results are not available yet. Please complete the upload and processing first."
            else:
                return False, f"Results not available in current state: {self.state}"
                
        else:
            return False, f"Unknown path: {path}"
        
        
class StateCheckRequest(BaseModel):
    path: str  # "form-upload", "log", or "result"
    user_id: str


class StateCheckResponse(BaseModel):
    allowed: bool
    reason: str
    current_state: str
    session_info: dict