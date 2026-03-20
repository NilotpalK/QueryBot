import json
import os
import uuid
from datetime import date
from typing import Optional

from bot.database import get_db


async def _load() -> dict:
    """Load the single hotel config document from MongoDB."""
    doc = await get_db()["hotel_config"].find_one({})
    if doc is None:
        raise RuntimeError(
            "No hotel config found in MongoDB. Run seed_mongo.py to upload hotel_data.json."
        )
    return doc


async def _save(data: dict):
    """Replace the hotel config document, stripping _id to avoid conflicts."""
    data.pop("_id", None)
    await get_db()["hotel_config"].replace_one({}, data)


# ── Hotel Info ───────────────────────────────────────────────────────────────

async def get_hotel_info() -> dict:
    return (await _load())["hotel"]


async def get_all_faqs() -> list[dict]:
    return (await _load())["faqs"]


# ── Rooms ────────────────────────────────────────────────────────────────────

async def get_all_rooms() -> list[dict]:
    return (await _load())["rooms"]


async def get_available_rooms(check_date: Optional[str] = None) -> list[dict]:
    rooms = await get_all_rooms()
    target = check_date or str(date.today())
    return [
        r for r in rooms
        if r["status"] == "available" and r["available_from"] <= target
    ]


async def get_rooms_by_type(room_type: str) -> list[dict]:
    rooms = await get_all_rooms()
    t = room_type.lower().strip()
    return [r for r in rooms if r["type"].lower() == t]


async def get_room_by_id(room_id: str) -> Optional[dict]:
    for r in await get_all_rooms():
        if r["id"] == room_id:
            return r
    return None


async def add_room(room: dict) -> dict:
    data = await _load()
    data["rooms"].append(room)
    await _save(data)
    return room


async def update_room(room_id: str, updates: dict) -> Optional[dict]:
    data = await _load()
    for i, r in enumerate(data["rooms"]):
        if r["id"] == room_id:
            data["rooms"][i].update(updates)
            await _save(data)
            return data["rooms"][i]
    return None


async def delete_room(room_id: str) -> bool:
    data = await _load()
    before = len(data["rooms"])
    data["rooms"] = [r for r in data["rooms"] if r["id"] != room_id]
    if len(data["rooms"]) < before:
        await _save(data)
        return True
    return False


# ── FAQs ─────────────────────────────────────────────────────────────────────

async def add_faq(faq: dict) -> dict:
    data = await _load()
    data["faqs"].append(faq)
    await _save(data)
    return faq


async def delete_faq(faq_id: str) -> bool:
    data = await _load()
    before = len(data["faqs"])
    data["faqs"] = [f for f in data["faqs"] if f["id"] != faq_id]
    if len(data["faqs"]) < before:
        await _save(data)
        return True
    return False


async def update_hotel_info(updates: dict) -> dict:
    data = await _load()
    data["hotel"].update(updates)
    await _save(data)
    return data["hotel"]
