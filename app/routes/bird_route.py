import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from app.auth_utils import get_current_user_data
from app.rabbitmq import send_rpc_request
from app.storage import upload_to_pinata

router = APIRouter(prefix="/bird", tags=["AILab"])
UPLOAD_DIR = Path("/app/shared_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png"}
AUDIO_SUFFIXES = {".mp3"}


@router.post("/analyze/{file_type}")
def analyze_file(file_type: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user_data)):
    if file_type not in ["photo", "audio"]:
        raise HTTPException(status_code=400, detail="Type 'photo' or 'audio'")

    filename = file.filename or "unknown"
    suffix = Path(filename).suffix.lower()

    allowed = PHOTO_SUFFIXES if file_type == "photo" else AUDIO_SUFFIXES
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Allowed: {allowed}")

    user_id = current_user["user_id"]
    safe_filename = f"{user_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        file_url = upload_to_pinata(str(file_path), safe_filename)
    except Exception as e:
        print(f"Error Pinata: {e}")
        file_url = None

    try:
        action = f"analyze_{file_type}"
        response = send_rpc_request({"action": action, "file_path": str(file_path), "user_id": user_id})

        if isinstance(response, dict):
            response["file_url"] = file_url

        return response
    except TimeoutError:
        raise HTTPException(status_code=504, detail="AI-server timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        file_path.unlink(missing_ok=True)
        pass


@router.get("/history")
def get_history(current_user: dict = Depends(get_current_user_data)):
    try:
        response = send_rpc_request({"action": "get_history"})
        if response.get("status") == "error":
            raise HTTPException(status_code=500, detail=response.get("message"))
        return response.get("data")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="AI-server timed out")

@router.get("/search")
def search_birds(name: str = Query(...), current_user: dict = Depends(get_current_user_data)):
    try:
        response = send_rpc_request({"action": "search_birds", "query": name})
        if response.get("status") == "error":
            raise HTTPException(status_code=500, detail=response.get("message"))
        return response.get("data")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="AI-server timed out")

@router.get("/statistics")
def get_statistics(current_user: dict = Depends(get_current_user_data)):
    try:
        response = send_rpc_request({"action": "get_statistics"})
        if response.get("status") == "error":
            raise HTTPException(status_code=500, detail=response.get("message"))
        return response.get("data")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="AI-server timed out")

@router.delete("/{record_id}")
def delete_bird(record_id: int, current_user: dict = Depends(get_current_user_data)):
    try:
        response = send_rpc_request({"action": "delete_bird", "record_id": record_id})
        if response.get("status") == "error":
            raise HTTPException(status_code=500, detail=response.get("message"))
        return response.get("data")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="AI-server timed out")