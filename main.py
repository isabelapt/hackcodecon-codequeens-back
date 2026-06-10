from dotenv import load_dotenv
load_dotenv()

import logging
import os
import sys
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(__file__))

from database import connect_db, close_db, get_db
from routers import tasks, cat, notifications
from services.notification_service import generate_useless_notification
from flask import Flask, g
from pymongo import MongoClient
from routers.flask_tasks import bp as flask_tasks_bp
from a2wsgi import WSGIMiddleware

scheduler = AsyncIOScheduler()


async def _scheduled_notification():
    try:
        db = get_db()
        await generate_useless_notification(db)
    except Exception:
        logger.exception("Scheduled notification generation failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    scheduler.add_job(_scheduled_notification, "interval", minutes=5, id="useless_notif")
    scheduler.start()
    yield
    scheduler.shutdown()
    await close_db()


app = FastAPI(
    title="Goose Cat 🐱",
    description="O gerenciador de tarefas que trabalha contra você.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api")
app.include_router(cat.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")

_MONGODB_URL = os.getenv("MONGODB_URL")
_MONGODB_DB = os.getenv("MONGODB_DB")

if not _MONGODB_URL:
    logger.warning("MONGODB_URL not set; Flask routes will fail to connect")
if not _MONGODB_DB:
    logger.warning("MONGODB_DB not set; Flask routes will use default database")

flask_app = Flask(__name__)
flask_app.register_blueprint(flask_tasks_bp)

@flask_app.before_request
def open_db():
    g.client = MongoClient(_MONGODB_URL)
    g.db = g.client[_MONGODB_DB]

@flask_app.teardown_appcontext
def close_db(exc):
    client = g.pop("client", None)
    if client:
        client.close()

app.mount("/flask", WSGIMiddleware(flask_app))

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/api/health")
def health():
    return {"status": "alive", "message": "Goose Cat está funcionando. Por enquanto."}
