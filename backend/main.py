"""FastAPI application: on-demand digest trigger + retrieval."""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import config
from cache import cache, inflight
from db import Base, SessionLocal, engine, get_db
from llm import llm
from models import Digest, Monitor, User
from pipeline import run_pipeline
from schemas import MonitorOut, TopicsIn

FIXED_USER_ID = 1
FIXED_USER_NAME = "Demo User"


def seed_user() -> None:
    db = SessionLocal()
    try:
        if db.get(User, FIXED_USER_ID) is None:
            db.add(User(id=FIXED_USER_ID, name=FIXED_USER_NAME, timezone="UTC"))
            db.commit()
    finally:
        db.close()


def require_api_key(x_api_key: str = Header(default="", alias="X-API-Key")):
    """Reject requests without the shared API key (when API_KEY is configured)."""
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

logger = logging.getLogger(__name__)


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _key(user_id: int, date: str) -> tuple:
    return (user_id, date)


def _is_fresh(generated_at: str | None) -> bool:
    if not generated_at:
        return False
    try:
        ts = datetime.fromisoformat(generated_at)
    except ValueError:
        return False
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    return 0 <= age < config.REFRESH_CACHE_TTL_SECONDS


def _get_digest(user_id: int, date: str, db: Session) -> dict | None:
    cached = cache.get(_key(user_id, date))
    if cached is not None:
        return cached
    digest = db.query(Digest).filter(Digest.user_id == user_id, Digest.date == date).first()
    if digest is None:
        return None
    cache.set(_key(user_id, date), digest.content)
    return digest.content


def _run_refresh_bg(user_id: int) -> None:
    db = SessionLocal()
    try:
        content = run_pipeline(user_id, db)
        cache.set(_key(user_id, content["date"]), content)
    except Exception:
        logger.exception("background refresh failed")
    finally:
        inflight.release(user_id)
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_user()
    yield


app = FastAPI(title="Daily News Digest", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/topics", response_model=list[MonitorOut], dependencies=[Depends(require_api_key)])
def list_topics(db: Session = Depends(get_db)):
    return db.query(Monitor).filter(Monitor.user_id == FIXED_USER_ID).order_by(Monitor.id).all()


@app.put("/topics", response_model=list[MonitorOut], dependencies=[Depends(require_api_key)])
def set_topics(payload: TopicsIn, db: Session = Depends(get_db)):
    db.query(Monitor).filter(Monitor.user_id == FIXED_USER_ID).delete()
    for topic in payload.topics:
        intent = llm.parse_intent(topic.raw_prompt)
        db.add(
            Monitor(
                user_id=FIXED_USER_ID,
                raw_prompt=topic.raw_prompt,
                keywords=intent["keywords"],
                categories=intent["categories"],
                sources=intent["sources"],
                data_requests=intent["data_requests"],
            )
        )
    db.commit()
    return db.query(Monitor).filter(Monitor.user_id == FIXED_USER_ID).order_by(Monitor.id).all()


@app.post("/refresh", dependencies=[Depends(require_api_key)])
def refresh(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    today = _today()

    cached = cache.get(_key(FIXED_USER_ID, today))
    if cached is not None:
        return cached

    digest = db.query(Digest).filter(Digest.user_id == FIXED_USER_ID, Digest.date == today).first()
    if digest is not None and _is_fresh(digest.content.get("generated_at")):
        cache.set(_key(FIXED_USER_ID, today), digest.content)
        return digest.content

    if not inflight.acquire(FIXED_USER_ID):
        return JSONResponse(status_code=202, content={"status": "pending"})

    background_tasks.add_task(_run_refresh_bg, FIXED_USER_ID)
    return JSONResponse(status_code=202, content={"status": "pending"})


@app.get("/digest/today", dependencies=[Depends(require_api_key)])
def digest_today(db: Session = Depends(get_db)):
    content = _get_digest(FIXED_USER_ID, _today(), db)
    if content is None:
        detail = (
            "refresh in progress; retry shortly"
            if inflight.is_active(FIXED_USER_ID)
            else "no digest yet; POST /refresh to generate"
        )
        raise HTTPException(status_code=404, detail=detail)
    return content


@app.get("/digest/{date}", dependencies=[Depends(require_api_key)])
def digest_by_date(date: str, db: Session = Depends(get_db)):
    content = _get_digest(FIXED_USER_ID, date, db)
    if content is None:
        raise HTTPException(status_code=404, detail=f"no digest for {date}")
    return content
