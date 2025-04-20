from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter(prefix="/ws", tags=["websocket"])

# Structure: { group_id: [WebSocket, WebSocket, ...] }
active_connections: Dict[str, List[WebSocket]] = {}

@router.websocket("/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: str):
    await websocket.accept()

    if group_id not in active_connections:
        active_connections[group_id] = []
    active_connections[group_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()  # keep connection open
    except WebSocketDisconnect:
        active_connections[group_id].remove(websocket)
        if not active_connections[group_id]:
            del active_connections[group_id]
