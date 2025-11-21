import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from bson import ObjectId
import shutil

from database import db, create_document
from schemas import PhotoSession, Photo

# Optional Google Drive integration
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

app = FastAPI(title="TrenchSight Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionCreate(BaseModel):
    site_name: str
    date: str
    start_lat: float
    start_lng: float
    device: Optional[str] = None
    battery_level: Optional[float] = None


@app.post("/api/sessions")
def create_session(payload: SessionCreate):
    session = PhotoSession(
        site_name=payload.site_name,
        date=payload.date,
        start_lat=payload.start_lat,
        start_lng=payload.start_lng,
        device=payload.device,
        battery_level=payload.battery_level,
        created_at=datetime.utcnow(),
    )
    session_id = create_document("photosession", session)
    return {"session_id": session_id}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        session = db["photosession"].find_one({"_id": ObjectId(session_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        # Convert ObjectId
        session["_id"] = str(session["_id"])
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Helper: Google Drive upload using service account json path in env
_drive_ready = False
_drive_service = None


def _init_drive():
    global _drive_ready, _drive_service
    if _drive_ready:
        return
    if not (GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_DRIVE_FOLDER_ID):
        _drive_ready = False
        return
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_JSON,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        _drive_service = build("drive", "v3", credentials=creds)
        _drive_ready = True
    except Exception:
        _drive_ready = False


def upload_to_drive(filename: str, filepath: str) -> Optional[str]:
    _init_drive()
    if not _drive_ready:
        return None
    try:
        from googleapiclient.http import MediaFileUpload
        file_metadata = {"name": filename, "parents": [GOOGLE_DRIVE_FOLDER_ID]}
        media = MediaFileUpload(filepath, mimetype="image/jpeg")
        file = _drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return file.get("id")
    except Exception:
        return None


@app.post("/api/photos")
async def upload_photo(
    session_id: str = Form(...),
    seq: int = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    tilt_deg: Optional[float] = Form(None),
    heading_deg: Optional[float] = Form(None),
    zoom: Optional[float] = Form(1.0),
    filename: str = Form(...),
    file: UploadFile = File(...),
):
    # Validate session exists
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    sess = db["photosession"].find_one({"_id": ObjectId(session_id)})
    if not sess:
        raise HTTPException(status_code=404, detail="Invalid session id")

    # Save file to local uploads directory
    uploads_dir = os.path.join("uploads", session_id)
    os.makedirs(uploads_dir, exist_ok=True)
    save_path = os.path.join(uploads_dir, filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Try upload to Google Drive
    drive_id = upload_to_drive(filename, save_path)

    # Record metadata in DB
    photo = Photo(
        session_id=session_id,
        seq=seq,
        lat=lat,
        lng=lng,
        tilt_deg=tilt_deg,
        heading_deg=heading_deg,
        zoom=zoom,
        filename=filename,
    )

    photo_id = create_document("photo", photo)

    return JSONResponse({
        "photo_id": photo_id,
        "drive_file_id": drive_id,
        "stored_path": save_path,
    })


@app.get("/")
def read_root():
    return {"message": "TrenchSight Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            collections = db.list_collection_names()
            response["collections"] = collections[:10]
            response["database"] = "✅ Connected & Working"
        else:
            response["database"] = "⚠️ Not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
