"""Optional chunked live endpoint placeholder; offline Whisper is not claimed as streaming."""

from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws/live")
async def live_transcription(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"status": "ready", "mode": "chunked", "note": "Send finalized local chunks; native streaming is not claimed."})
    await websocket.close()
