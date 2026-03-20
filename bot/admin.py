import os
import uuid
from fastapi import APIRouter, HTTPException, Depends, Header
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


# ── Hotel Info ───────────────────────────────────────────────────────────────

@router.get("/hotel")
async def get_hotel(auth=Depends(verify_admin)):
    return await get_hotel_info()


@router.patch("/hotel")
async def patch_hotel(updates: dict, auth=Depends(verify_admin)):
    return await update_hotel_info(updates)


# ── Rooms ────────────────────────────────────────────────────────────────────

@router.get("/rooms")
async def list_rooms(auth=Depends(verify_admin)):
    return await get_all_rooms()


@router.post("/rooms")
async def create_room(room: dict, auth=Depends(verify_admin)):
    if "id" not in room:
        room["id"] = str(uuid.uuid4())[:6].upper()
    if "status" not in room:
        room["status"] = "available"
    return await add_room(room)


@router.put("/rooms/{room_id}")
async def edit_room(room_id: str, updates: dict, auth=Depends(verify_admin)):
    updated = await update_room(room_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return updated


@router.delete("/rooms/{room_id}")
async def remove_room(room_id: str, auth=Depends(verify_admin)):
    ok = await delete_room(room_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return {"deleted": room_id}


# ── FAQs ─────────────────────────────────────────────────────────────────────

@router.get("/faqs")
async def list_faqs(auth=Depends(verify_admin)):
    return await get_all_faqs()


@router.post("/faqs")
async def create_faq(faq: dict, auth=Depends(verify_admin)):
    if "id" not in faq:
        faq["id"] = f"f{uuid.uuid4().hex[:6]}"
    return await add_faq(faq)


@router.delete("/faqs/{faq_id}")
async def remove_faq(faq_id: str, auth=Depends(verify_admin)):
    ok = await delete_faq(faq_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"FAQ {faq_id} not found")
    return {"deleted": faq_id}


# ── Conversation Logs ────────────────────────────────────────────────────────

@router.get("/logs")
async def conversation_logs(auth=Depends(verify_admin)):
    return await get_conversation_log()


@router.delete("/sessions/{phone}")
async def reset_session(phone: str, auth=Depends(verify_admin)):
    await clear_session(phone)
    return {"cleared": phone}
