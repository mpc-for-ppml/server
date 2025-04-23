from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from .sessions import _sessions
import json

router = APIRouter(prefix="/ws", tags=["websocket"])

# Structure: { group_id: [WebSocket, WebSocket, ...] }
active_connections: Dict[str, List[WebSocket]] = {}

@router.websocket("/{session_id}")
async def ws_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()
    
    sess = _sessions.get(session_id)
    if not sess:
        await ws.close(code=1008)  # policy violation
        return

    try:
        while True:
            text = await ws.receive_text()
            msg = json.loads(text)
            uid, status = msg["userId"], msg["status"]

            # first time we see this user: enforce capacity
            if uid not in sess["joined"]:
                if len(sess["joined"]) >= sess["participant_count"]:
                    await ws.send_text(json.dumps({"error":"session full"}))
                    continue
                sess["joined"].add(uid)

            # update their ready‐status
            sess["status_map"][uid] = bool(status)

            # broadcast updated map
            payload = json.dumps({"statusMap": sess["status_map"]})
            for client in active_connections.setdefault(session_id, []):
                await client.send_text(payload)

            # add this socket to the room if new
            if ws not in active_connections[session_id]:
                active_connections[session_id].append(ws)

    except WebSocketDisconnect:
        active_connections[session_id].remove(ws)
        # optionally cleanup sess["joined"] & status_map on disconnect