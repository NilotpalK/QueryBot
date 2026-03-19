import json
import os
from datetime import date
from typing import Optional

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "hotel_data.json")


def _load() -> dict:
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _save(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Hotel Info ──────────────────────────────────────────────────────────────

def get_hotel_info() -> dict:
    return _load()["hotel"]


def get_all_faqs() -> list[dict]:
    return _load()["faqs"]


# ── Rooms ───────────────────────────────────────────────────────────────────

def get_all_rooms() -> list[dict]:
    return _load()["rooms"]


def get_available_rooms(check_date: Optional[str] = None) -> list[dict]:
    """
    Returns rooms that are available on or before check_date.
    check_date: ISO date string (YYYY-MM-DD). Defaults to today.
    """
    rooms = _load()["rooms"]
    target = check_date or str(date.today())
    available = []
    for room in rooms:
        if room["status"] == "available" and room["available_from"] <= target:
            available.append(room)
    return available


def get_rooms_by_type(room_type: str) -> list[dict]:
    rooms = _load()["rooms"]
    t = room_type.lower().strip()
    return [r for r in rooms if r["type"].lower() == t]


def get_room_by_id(room_id: str) -> Optional[dict]:
    rooms = _load()["rooms"]
    for r in rooms:
        if r["id"] == room_id:
            return r
    return None


def add_room(room: dict) -> dict:
    data = _load()
    data["rooms"].append(room)
    _save(data)
    return room


def update_room(room_id: str, updates: dict) -> Optional[dict]:
    data = _load()
    for i, r in enumerate(data["rooms"]):
        if r["id"] == room_id:
            data["rooms"][i].update(updates)
            _save(data)
            return data["rooms"][i]
    return None


def delete_room(room_id: str) -> bool:
    data = _load()
    before = len(data["rooms"])
    data["rooms"] = [r for r in data["rooms"] if r["id"] != room_id]
    if len(data["rooms"]) < before:
        _save(data)
        return True
    return False


# ── FAQs ────────────────────────────────────────────────────────────────────

def add_faq(faq: dict) -> dict:
    data = _load()
    data["faqs"].append(faq)
    _save(data)
    return faq


def delete_faq(faq_id: str) -> bool:
    data = _load()
    before = len(data["faqs"])
    data["faqs"] = [f for f in data["faqs"] if f["id"] != faq_id]
    if len(data["faqs"]) < before:
        _save(data)
        return True
    return False


def update_hotel_info(updates: dict) -> dict:
    data = _load()
    data["hotel"].update(updates)
    _save(data)
    return data["hotel"]
