import json
import os
from typing import Optional
from interface.result import SessionResult
from utils.constant import RESULT_DIR

class ResultService:
    @staticmethod
    def save_result(session_id: str, result_data: dict) -> None:
        """Save computation results for a session"""
        os.makedirs(RESULT_DIR, exist_ok=True)
        
        result_file = os.path.join(RESULT_DIR, f"{session_id}.json")
        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2)
    
    @staticmethod
    def get_result(session_id: str) -> Optional[SessionResult]:
        """Retrieve computation results for a session"""
        result_file = os.path.join(RESULT_DIR, f"{session_id}.json")
        
        if not os.path.exists(result_file):
            return None
        
        with open(result_file, "r") as f:
            data = json.load(f)
        
        return SessionResult(**data)
    
    @staticmethod
    def result_exists(session_id: str) -> bool:
        """Check if results exist for a session"""
        result_file = os.path.join(RESULT_DIR, f"{session_id}.json")
        return os.path.exists(result_file)