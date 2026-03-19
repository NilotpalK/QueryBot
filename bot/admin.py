import os
import uuid
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional

from bot.hotel_service import (
    get_all_rooms, add_room, update_room, delete_room,
    get_all_faqs, add_faq, delete_faq,
    get_hotel_info, update_hotel_info,
)
from bot.agent import get_conversation_log, clear_session

router = APIRouter(prefix="/admin")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")


def verify_admin(x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")


# ── Hotel Info ──────────────────────────────────────────────────────────────

@router.get("/hotel")
def get_hotel(auth=Depends(verify_admin)):
    return get_hotel_info()


@router.patch("/hotel")
def patch_hotel(updates: dict, auth=Depends(verify_admin)):
    return update_hotel_info(updates)


# ── Rooms ───────────────────────────────────────────────────────────────────

@router.get("/rooms")
def list_rooms(auth=Depends(verify_admin)):
    return get_all_rooms()


@router.post("/rooms")
def create_room(room: dict, auth=Depends(verify_admin)):
    if "id" not in room:
        room["id"] = str(uuid.uuid4())[:6].upper()
    if "status" not in room:
        room["status"] = "available"
    return add_room(room)


@router.put("/rooms/{room_id}")
def edit_room(room_id: str, updates: dict, auth=Depends(verify_admin)):
    updated = update_room(room_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return updated


@router.delete("/rooms/{room_id}")
def remove_room(room_id: str, auth=Depends(verify_admin)):
    ok = delete_room(room_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return {"deleted": room_id}


# ── FAQs ────────────────────────────────────────────────────────────────────

@router.get("/faqs")
def list_faqs(auth=Depends(verify_admin)):
    return get_all_faqs()


@router.post("/faqs")
def create_faq(faq: dict, auth=Depends(verify_admin)):
    if "id" not in faq:
        faq["id"] = f"f{uuid.uuid4().hex[:6]}"
    return add_faq(faq)


@router.delete("/faqs/{faq_id}")
def remove_faq(faq_id: str, auth=Depends(verify_admin)):
    ok = delete_faq(faq_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"FAQ {faq_id} not found")
    return {"deleted": faq_id}


# ── Conversation Logs ────────────────────────────────────────────────────────

@router.get("/logs")
def conversation_logs(auth=Depends(verify_admin)):
    return get_conversation_log()


@router.delete("/sessions/{phone}")
def reset_session(phone: str, auth=Depends(verify_admin)):
    clear_session(phone)
    return {"cleared": phone}
