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


# ── Bookings ─────────────────────────────────────────────────────────────────

@router.get("/bookings")
async def list_bookings(room_id: str = None, auth=Depends(verify_admin)):
    from bot.database import get_db
    query = {}
    if room_id:
        query["room_id"] = room_id
    cursor = get_db()["bookings"].find(query, {"_id": 1, "room_id": 1, "guest_name": 1,
                                              "guest_phone": 1, "check_in": 1, "check_out": 1,
                                              "notes": 1, "created_at": 1})
    return await cursor.to_list(length=500)


@router.post("/bookings")
async def create_booking(booking: dict, auth=Depends(verify_admin)):
    from bot.database import get_db
    from bson.objectid import ObjectId
    from datetime import datetime
    required = {"room_id", "guest_name", "check_in", "check_out"}
    if not required.issubset(booking):
        raise HTTPException(status_code=400, detail=f"Missing fields: {required - booking.keys()}")
    booking["_id"] = str(ObjectId())
    booking["created_at"] = datetime.now().isoformat()
    await get_db()["bookings"].insert_one(booking)
    return booking


@router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, auth=Depends(verify_admin)):
    from bot.database import get_db
    result = await get_db()["bookings"].delete_one({"_id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"cancelled": booking_id}
