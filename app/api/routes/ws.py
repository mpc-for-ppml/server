from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .state import _sessions, active_connections
from utils.data_loader import ensure_log_file_exists
from utils.constant import LOG_FILE
import json
import asyncio
import os
import re

router = APIRouter(prefix="/ws", tags=["websocket"])
process_ref = None

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
            uid = msg.get("userId")
            status = msg.get("status", None)
            proceed = msg.get("proceed", False)

            # First time we see this user: enforce capacity
            if uid not in sess["joined"]:
                if len(sess["joined"]) >= sess["participant_count"]:
                    await ws.send_text(json.dumps({"error":"session full"}))
                    continue
                sess["joined"].add(uid)
            
            # Update user status if provided
            if status is not None:
                sess["status_map"][uid] = bool(status)
                
            # Add socket to active room
            if ws not in active_connections.setdefault(session_id, []):
                active_connections[session_id].append(ws)
                
            # Prepare broadcast payload
            broadcast_payload = {}
            if status is not None:
                broadcast_payload["statusMap"] = sess["status_map"]
            if proceed:
                broadcast_payload["proceed"] = True

            # Broadcast to all connected clients
            if broadcast_payload:
                for client in active_connections[session_id]:
                    await client.send_text(json.dumps(broadcast_payload))

    except WebSocketDisconnect:
        active_connections[session_id].remove(ws)
        # optionally cleanup sess["joined"] & status_map on disconnect