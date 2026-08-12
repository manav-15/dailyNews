"""FastAPI application: on-demand digest trigger + retrieval."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

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


@app.get("/topics", response_model=list[MonitorOut])
def list_topics(db: Session = Depends(get_db)):
    return db.query(Monitor).filter(Monitor.user_id == FIXED_USER_ID).order_by(Monitor.id).all()


@app.put("/topics", response_model=list[MonitorOut])
def set_topics(payload: TopicsIn, db: Session = Depends(get_db)):
    # Replace the user's monitors with freshly-parsed versions.
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


@app.post("/refresh")
def refresh(db: Session = Depends(get_db)):
    """Run the pipeline on demand and return the freshly generated digest."""
    return run_pipeline(FIXED_USER_ID, db)


@app.get("/digest/today")
def digest_today(db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date().isoformat()
    digest = db.query(Digest).filter(Digest.user_id == FIXED_USER_ID, Digest.date == today).first()
    if digest is None:
        raise HTTPException(status_code=404, detail="no digest yet; POST /refresh to generate")
    return digest.content


@app.get("/digest/{date}")
def digest_by_date(date: str, db: Session = Depends(get_db)):
    digest = db.query(Digest).filter(Digest.user_id == FIXED_USER_ID, Digest.date == date).first()
    if digest is None:
        raise HTTPException(status_code=404, detail=f"no digest for {date}")
    return digest.content
