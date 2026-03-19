import os
import json
import httpx
from collections import defaultdict, deque
from datetime import datetime

from bot.hotel_service import (
    get_hotel_info,
    get_all_faqs,
    get_available_rooms,
    get_all_rooms,
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Per-number conversation history (keeps last 10 exchanges)
_sessions: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))

# ── Conversation log (for admin) ────────────────────────────────────────────
_conversation_log: list[dict] = []


def _build_system_prompt() -> str:
    hotel = get_hotel_info()
    rooms = get_all_rooms()
    faqs = get_all_faqs()
    available = get_available_rooms()

    # Summarise room inventory
    room_summary_lines = []
    for r in rooms:
        status_label = {
            "available": "✅ Available",
            "occupied": "🔴 Occupied",
            "maintenance": "🔧 Maintenance",
        }.get(r["status"], r["status"].title())
        line = (
            f"  - Room {r['id']} ({r['type']}, {r['bed_type']}, {r['view']}): "
            f"₹{r['price_per_night']}/night, Max {r['max_occupancy']} guests, "
            f"{status_label}. Available from: {r['available_from']}. "
            f"Features: {', '.join(r['features'])}."
        )
        room_summary_lines.append(line)

    faq_lines = "\n".join(
        f"  Q: {f['question']}\n  A: {f['answer']}" for f in faqs
    )

    amenities_str = ", ".join(hotel.get("amenities", []))

    prompt = f"""You are a friendly, professional hotel concierge bot for {hotel['name']}.
Your job is to assist hotel guests over WhatsApp by answering their questions clearly and helpfully.

=== HOTEL INFO ===
Name: {hotel['name']}
Address: {hotel['address']}
Phone: {hotel['phone']}
Email: {hotel['email']}
Check-in Time: {hotel['check_in_time']}
Check-out Time: {hotel['check_out_time']}
Amenities: {amenities_str}
Cancellation Policy: {hotel['cancellation_policy']}
Pet Policy: {hotel['pet_policy']}
Smoking Policy: {hotel['smoking_policy']}
Extra Bed Charge: {hotel['extra_bed_charge']}
Breakfast: {'Included' if hotel['breakfast_included'] else f"Not included. Optional add-on: {hotel['breakfast_charge']}"}

=== ROOM INVENTORY ===
{chr(10).join(room_summary_lines)}

=== CURRENTLY AVAILABLE ROOMS ({len(available)} rooms) ===
{json.dumps([{'id': r['id'], 'type': r['type'], 'price': r['price_per_night'], 'view': r['view'], 'bed_type': r['bed_type']} for r in available], indent=2)}

=== FAQS ===
{faq_lines}

=== YOUR INSTRUCTIONS ===
- Answer in a warm, concise, professional tone.
- Always use Indian Rupee (₹) for prices.
- If asked about room availability, use the ROOM INVENTORY above.
- If a specific room type is requested that is fully occupied, tell the guest when it becomes available.
- If you cannot answer something, politely say so and suggest they call the hotel directly at {hotel['phone']}.
- Do NOT make up information not listed above.
- Keep responses short enough to read comfortably on a mobile screen (2-4 sentences max, unless listing details).
- Today's date is {datetime.now().strftime('%B %d, %Y')}.
"""
    return prompt


def get_reply(phone_number: str, user_message: str) -> str:
    """
    Given an incoming WhatsApp message, returns the AI reply.
    Maintains per-number conversation history.
    """
    history = _sessions[phone_number]

    # Add user message to history
    history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": _build_system_prompt()}]
    messages.extend(list(history))

    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://querybot.hotel",
                "X-Title": "Hotel Query Bot",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.5,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        reply = (
            "Sorry, I'm having trouble connecting right now. "
            "Please call us directly at the hotel number for immediate assistance."
        )
        print(f"[Agent Error] {e} | Response body: {e.response.text}")
    except Exception as e:
        reply = (
            "Sorry, I'm having trouble connecting right now. "
            "Please call us directly at the hotel number for immediate assistance."
        )
        print(f"[Agent Error] {e}")

    # Add assistant reply to history
    history.append({"role": "assistant", "content": reply})

    # Log the conversation
    _conversation_log.append({
        "phone": phone_number,
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "bot": reply,
    })

    return reply


def get_conversation_log() -> list[dict]:
    return list(reversed(_conversation_log))


def clear_session(phone_number: str):
    if phone_number in _sessions:
        del _sessions[phone_number]
