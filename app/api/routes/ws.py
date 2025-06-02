from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .state import _sessions, active_connections
from utils.constant import LOG_DIR
from interface.session_state import SessionState
from services.file_service import ensure_log_file_exists
from datetime import datetime
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
            training = msg.get("training", False)

            # First time we see this user: enforce capacity
            if uid not in sess.joined_users:
                if len(sess.joined_users) >= sess.participant_count:
                    await ws.send_text(json.dumps({"error":"session full"}))
                    continue
                sess.joined_users.add(uid)
                sess.updated_at = datetime.now()
                
                # Update state to UPLOADING when first user joins
                if sess.state == SessionState.CREATED:
                    sess.state = SessionState.UPLOADING
                    sess.updated_at = datetime.now()
            
            # Update user status if provided
            if status is not None:
                sess.status_map[uid] = bool(status)
                sess.updated_at = datetime.now()
                
            # Add socket to active room
            if ws not in active_connections.setdefault(session_id, []):
                active_connections[session_id].append(ws)
                
            # Prepare broadcast payload
            broadcast_payload = {}
            if status is not None:
                broadcast_payload["statusMap"] = sess.status_map
            if proceed:
                broadcast_payload["proceed"] = True
            if training:
                broadcast_payload["training"] = True

            # Broadcast to all connected clients
            if broadcast_payload:
                for client in active_connections[session_id]:
                    await client.send_text(json.dumps(broadcast_payload))

    except WebSocketDisconnect:
        active_connections[session_id].remove(ws)
        # optionally cleanup sess["joined"] & status_map on disconnect


@router.websocket("/{session_id}/progress/{user_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str, user_id: str):
    await ws.accept()
    print(f"🔌 WebSocket connected for user {user_id}")
    
    sess = _sessions.get(session_id)
    if not sess:
        await ws.close(code=1008)  # policy violation
        return
    
    # Check if user is part of the session
    if user_id not in sess.joined_users:
        await ws.send_text("⚠️ Error: User not part of this session")
        await ws.close(code=1008)
        return

    try:
        # Use user-specific log file
        ensure_log_file_exists(session_id)
        log_file_path = os.path.join(LOG_DIR, session_id, f"log_{user_id}.log")
        
        # Create log file if it doesn't exist
        if not os.path.exists(log_file_path):
            with open(log_file_path, "w", encoding="utf-8"):
                pass

        with open(log_file_path, "r", encoding="utf-8") as f:
            f.seek(0, os.SEEK_END)  # Start tailing from the end
            
            has_output = False  # Track if we have sent any output
            milestone_final = "✅ MPyc task complete"
            sent_final = False
            
            party_log_pattern = re.compile(r"^\[Party \d+] ")

            while True:            
                line = f.readline()
                if line:
                    cleaned_line = line.strip()
                    
                    # Filter: only send lines that start with [Party X]
                    if not party_log_pattern.match(cleaned_line):
                        continue
                    
                    await ws.send_text(cleaned_line)
                    has_output = True

                    if cleaned_line == milestone_final:
                        sent_final = True
                else:
                    await asyncio.sleep(0.5)

                # End WebSocket when dummy_task.py ends
                if process_ref and process_ref.poll() is not None and has_output and sent_final:
                    await ws.send_text("🛑 MPyC shutdown")
                    await ws.close()
                    break

    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnected for user {user_id}")
    except Exception as e:
        await ws.send_text(f"⚠️ Error: {str(e)}")
        await ws.close()