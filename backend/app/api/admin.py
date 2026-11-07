from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile

from agent.runtime import build_rag_stack, reset_voice_rag
from app.auth import check_login, clear_session_cookie, current_admin, make_session_token, set_session_cookie
from app.config import KNOWLEDGE_DIR
from app.db import get_asset, list_assets
from app.seaweed import read_recording
from app.schemas import AdminLoginRequest

router = APIRouter()
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")
_ALLOWED = {".md", ".txt"}


def _safe_name(name: str) -> str:
    raw = Path(name or "").name
    stem = _SAFE.sub("-", Path(raw).stem).strip(".-") or "note"
    suffix = Path(raw).suffix.lower()
    if suffix not in _ALLOWED:
        raise HTTPException(status_code=400, detail="Upload .md or .txt files only.")
    return f"{stem}{suffix}"


def _list_docs() -> list[dict]:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(KNOWLEDGE_DIR.glob("*.md")) + sorted(KNOWLEDGE_DIR.glob("*.txt"))
    return [
        {"name": path.name, "bytes": path.stat().st_size, "updated": int(path.stat().st_mtime)}
        for path in files
    ]


def _rebuild_chat(request: Request) -> None:
    request.app.state.graph = build_rag_stack(for_voice=False)
    request.app.state.ready = True
    request.app.state.error = None
    reset_voice_rag()


@router.post("/admin/login")
def login(body: AdminLoginRequest, response: Response):
    username = body.username.strip()
    check_login(username, body.password)
    token = make_session_token(username)
    set_session_cookie(response, token)
    return {"ok": True, "username": username, "token": token}


@router.post("/admin/logout")
def logout(response: Response):
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/admin/me")
def me(username: str = Depends(current_admin)):
    return {"ok": True, "username": username}


@router.get("/admin/documents")
def documents(_: str = Depends(current_admin)):
    return {"documents": _list_docs()}


@router.get("/admin/assets")
def assets(_: str = Depends(current_admin)):
    return {"assets": list_assets()}


@router.get("/admin/assets/{asset_id}/audio")
def asset_audio(asset_id: int, _: str = Depends(current_admin)):
    asset = get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Recording not found.")
    try:
        data = read_recording(str(asset["storage_path"]))
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Recording file is missing.") from exc
    filename = f"{asset['room'] or 'call'}.wav"
    return Response(
        content=data,
        media_type=str(asset.get("mime_type") or "audio/wav"),
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/admin/documents")
async def upload_documents(
    request: Request,
    files: list[UploadFile] = File(...),
    _: str = Depends(current_admin),
):
    if not files:
        raise HTTPException(status_code=400, detail="Choose at least one file.")
    saved: list[str] = []
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    for upload in files:
        name = _safe_name(upload.filename or "note.md")
        target = KNOWLEDGE_DIR / name
        data = await upload.read()
        if not data.strip():
            continue
        target.write_bytes(data)
        saved.append(name)
    if not saved:
        raise HTTPException(status_code=400, detail="No readable files were uploaded.")
    try:
        _rebuild_chat(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Files saved but reindex failed: {exc}") from exc
    return {"ok": True, "saved": saved, "documents": _list_docs()}


@router.delete("/admin/documents/{name}")
def delete_document(name: str, request: Request, _: str = Depends(current_admin)):
    path = KNOWLEDGE_DIR / Path(name).name
    if path.suffix.lower() not in _ALLOWED or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")
    remaining = list(KNOWLEDGE_DIR.glob("*.md")) + list(KNOWLEDGE_DIR.glob("*.txt"))
    if len(remaining) <= 1:
        raise HTTPException(status_code=400, detail="Keep at least one knowledge file.")
    path.unlink()
    try:
        _rebuild_chat(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"File removed but reindex failed: {exc}") from exc
    return {"ok": True, "documents": _list_docs()}
