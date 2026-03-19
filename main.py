import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from bot.webhook import router as webhook_router
from bot.admin import router as admin_router

app = FastAPI(
    title="Hotel WhatsApp Bot",
    description="AI-powered WhatsApp bot for hotel guest queries",
    version="1.0.0",
)

# ── API Routes ───────────────────────────────────────────────────────────────
app.include_router(webhook_router)
app.include_router(admin_router)

# ── Serve Admin Dashboard (static files) ────────────────────────────────────
DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "dashboard")
app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")


@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))


@app.get("/", include_in_schema=False)
async def root():
    return {
        "status": "running",
        "bot": "Hotel WhatsApp Query Bot",
        "dashboard": "/dashboard",
        "docs": "/docs",
        "webhook": "/webhook",
        "test_endpoint": "/webhook/test",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
