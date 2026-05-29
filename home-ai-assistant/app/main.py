import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import chat, expenses, locations, manuals, reminders, vault
from app.routers.voice import manager, router as voice_router
from app.services.scheduler import get_scheduler, restore_reminder_jobs, set_broadcast_fn

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "manuals"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting 家庭AI助理...")
    init_db()

    set_broadcast_fn(manager.broadcast)
    scheduler = get_scheduler()
    scheduler.start()
    restore_reminder_jobs()
    app.state.scheduler = scheduler
    app.state.vault_sessions = {}

    logger.info("家庭AI助理已启动，访问 http://0.0.0.0:8080")
    yield

    scheduler.shutdown()
    logger.info("家庭AI助理已停止")


app = FastAPI(
    title="家庭AI助理",
    description="智能家庭管理助理",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(voice_router)
app.include_router(manuals.router)
app.include_router(vault.router)
app.include_router(locations.router)
app.include_router(expenses.router)
app.include_router(reminders.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/system/info")
def system_info():
    return {
        "version": "1.0.0",
        "whisper_model": settings.WHISPER_MODEL,
        "tts_voice": settings.TTS_VOICE,
    }


# Serve frontend — must be last
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
