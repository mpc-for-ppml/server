from typing import Dict, List
from fastapi import WebSocket

# shared state
# In-memory store for demo; swap out for a real DB
_sessions: dict[str, dict] = {}
# Structure: { group_id: [WebSocket, WebSocket, ...] }
active_connections: Dict[str, List[WebSocket]] = {}