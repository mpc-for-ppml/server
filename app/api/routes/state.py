from typing import Dict, List
from fastapi import WebSocket
from interface.session_state import SessionStateInfo

# shared state
# In-memory store for demo; swap out for a real DB
_sessions: Dict[str, SessionStateInfo] = {}
# Structure: { group_id: [WebSocket, WebSocket, ...] }
active_connections: Dict[str, List[WebSocket]] = {}