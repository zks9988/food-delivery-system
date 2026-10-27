"""
Unstructured Data Storage Routes
- Stores images, documents, audio as files
- Stores JSON data in database
- Supports Big Data storage patterns
"""
import os
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from models import get_db, Review, AuditLog
from auth import get_current_user

from config import UNSTRUCTURED_STORAGE_PATH

router = APIRouter(prefix="/api/unstructured", tags=["Unstructured Data"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...),
                      category: str = Form("general"),
                      user=Depends(get_current_user)):
    """Upload unstructured data (images, documents, etc.)"""
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] if file.filename else ".bin"
    safe_name = f"{file_id}{ext}"

    category_dir = os.path.join(UNSTRUCTURED_STORAGE_PATH, category)
    os.makedirs(category_dir, exist_ok=True)
    file_path = os.path.join(category_dir, safe_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    metadata = {
        "file_id": file_id,
        "original_name": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "category": category,
        "uploaded_by": user.id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "storage_path": file_path,
        "tags": []  # For future indexing in Big Data system
    }

    meta_path = file_path + ".meta.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size_bytes": len(content),
        "metadata": metadata,
        "message": "File stored as unstructured data"
    }

@router.get("/list")
def list_unstructured(category: Optional[str] = None,
                      user=Depends(get_current_user)):
    """List stored unstructured data"""
    search_dir = os.path.join(UNSTRUCTURED_STORAGE_PATH, category) if category else UNSTRUCTURED_STORAGE_PATH

    if not os.path.exists(search_dir):
        return {"files": []}

    files = []
    for f in os.listdir(search_dir):
        if f.endswith(".meta.json"):
            with open(os.path.join(search_dir, f)) as mf:
                files.append(json.load(mf))

    return {"files": files, "category": category or "all", "count": len(files)}

@router.get("/download/{file_id}")
def download_file(file_id: str, category: str = "general",
                  user=Depends(get_current_user)):
    """Download stored unstructured data"""
    category_dir = os.path.join(UNSTRUCTURED_STORAGE_PATH, category)
    if not os.path.exists(category_dir):
        raise HTTPException(404, "File not found")

    for f in os.listdir(category_dir):
        if f.startswith(file_id) and not f.endswith(".meta.json"):
            file_path = os.path.join(category_dir, f)
            # Try to get original name from metadata
            meta_path = file_path + ".meta.json"
            original_name = f
            if os.path.exists(meta_path):
                with open(meta_path) as mf:
                    meta = json.load(mf)
                    original_name = meta.get("original_name", f)
            return FileResponse(file_path, filename=original_name)

    raise HTTPException(404, "File not found")
