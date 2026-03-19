# 🏨 QueryBot — WhatsApp Hotel Query Bot

An AI-powered WhatsApp bot for hotels. Guests send WhatsApp messages and get instant replies about **room availability, pricing, check-in/out times, amenities, FAQs**, and more. Backed by a slick **admin dashboard** to manage everything.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| AI | OpenRouter (any LLM — default: `mistralai/mistral-7b-instruct`) |
| WhatsApp | Twilio WhatsApp API |
| Dashboard | Vanilla HTML/CSS/JS (glassmorphism dark UI) |
| Data Store | `hotel_data.json` (file-based, no DB required) |

---

## Project Structure

```
QueryBot/
├── main.py                  # FastAPI app entry point
├── hotel_data.json          # Hotel info, rooms & FAQs
├── requirements.txt
├── .env.example             # Copy to .env and fill in
├── bot/
│   ├── agent.py             # OpenRouter AI + session memory
│   ├── hotel_service.py     # Room/FAQ CRUD against hotel_data.json
│   ├── webhook.py           # Twilio WhatsApp webhook handler
│   └── admin.py             # Password-protected admin REST API
└── dashboard/
    ├── index.html           # Admin dashboard UI
    ├── style.css
    └── app.js
```

---

## Quick Start

### 1. Clone & Install

```bash
cd /Users/nilotpal/Desktop/Personal/QueryBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|----------|----------------|
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) → Keys |
| `OPENROUTER_MODEL` | Default: `mistralai/mistral-7b-instruct` (free) |
| `TWILIO_ACCOUNT_SID` | [console.twilio.com](https://console.twilio.com) |
| `TWILIO_AUTH_TOKEN` | Twilio Console |
| `TWILIO_WHATSAPP_FROM` | Twilio sandbox: `whatsapp:+14155238886` |
| `ADMIN_PASSWORD` | Any password you choose |

### 3. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

---

## Connecting WhatsApp (Twilio Sandbox)

1. Sign up free at [twilio.com](https://twilio.com)
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Follow the sandbox join instructions (send a WhatsApp to the sandbox number)
4. Install [ngrok](https://ngrok.com): `brew install ngrok`
5. Expose your local server:
   ```bash
   ngrok http 8000
   ```
6. Copy the `https://xxxx.ngrok.io` URL
7. In Twilio Console → WhatsApp Sandbox → **Webhook URL**:
   ```
   https://xxxx.ngrok.io/webhook
   ```
8. Save → Message the sandbox number from WhatsApp 🎉

---

## Testing Without WhatsApp

Use the built-in **Test Bot** tab in the dashboard, or `curl` directly:

```bash
curl -X POST http://localhost:8000/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "message": "Is a deluxe room available tonight?"}'
```

---

## Admin Dashboard

Open http://localhost:8000/dashboard and log in with your `ADMIN_PASSWORD`.

| Tab | What you can do |
|-----|----------------|
| 📊 Overview | Hotel info, room stats summary |
| 🛏️ Rooms | Add, edit, delete rooms, toggle availability |
| ❓ FAQs | Add / delete Q&A pairs the bot will use |
| 💬 Conversations | Full WhatsApp conversation history grouped by number |
| 🧪 Test Bot | Chat with the bot directly in your browser |

---

## Customising the Hotel

Edit `hotel_data.json` directly or use the Admin API:

```bash
# Update hotel info
curl -X PATCH http://localhost:8000/admin/hotel \
  -H "x-admin-password: changeme123" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Hotel", "check_in_time": "3:00 PM"}'

# Add a room
curl -X POST http://localhost:8000/admin/rooms \
  -H "x-admin-password: changeme123" \
  -H "Content-Type: application/json" \
  -d '{"id":"501","type":"Suite","price_per_night":12000,"max_occupancy":4,"bed_type":"King","view":"Sea View","status":"available","available_from":"2026-03-19","features":["AC","Jacuzzi","Wi-Fi"]}'
```

---

## Switching AI Models (OpenRouter)

Change `OPENROUTER_MODEL` in `.env` to any model from [openrouter.ai/models](https://openrouter.ai/models):

| Model | Notes |
|-------|-------|
| `mistralai/mistral-7b-instruct` | Free, fast, good quality |
| `google/gemma-3-27b-it:free` | Free Google model |
| `anthropic/claude-3-haiku` | Paid, very high quality |
| `openai/gpt-4o-mini` | Paid, great balance |
