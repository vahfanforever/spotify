import os
from datetime import datetime

import spotipy
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Database Models
Base = declarative_base()


class UserToken(Base):
    __tablename__ = "user_tokens"

    user_id = Column(String, primary_key=True)
    access_token = Column(String, nullable=False)
    date_added = Column(DateTime, default=datetime.utcnow)


class SongMapping(Base):
    __tablename__ = "song_mappings"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user_tokens.user_id"))
    trigger_song_id = Column(String, nullable=False)
    queue_song_id = Column(String, nullable=False)


# Pydantic Models
class UserTokenCreate(BaseModel):
    user_id: str
    access_token: str


class UserTokenUpdate(BaseModel):
    access_token: str


class SongMappingCreate(BaseModel):
    trigger_song_id: str
    queue_song_id: str


class CurrentSongRequest(BaseModel):
    song_id: str


# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.post("/users/token")
async def create_user_token(
    token: UserTokenCreate,  # Changed to use Pydantic model as request body
    db: Session = Depends(get_db),
):
    """Create a new user token. Fails if user already exists."""
    # Check if user already exists
    existing_user = db.query(UserToken).filter(UserToken.user_id == token.user_id).first()
    if existing_user:
        raise HTTPException(
            status_code=409, detail="User already exists. Use PUT /users/{user_id}/token to update."
        )

    # Create UserToken instance from Pydantic model
    user = UserToken(user_id=token.user_id, access_token=token.access_token)

    db.add(user)
    db.commit()
    return {"status": "success", "user_id": user.user_id}


@app.put("/users/{user_id}/token")
async def update_user_token(user_id: str, token: UserTokenUpdate, db: Session = Depends(get_db)):
    user = UserToken(user_id=user_id, access_token=token.access_token)
    db.merge(user)
    db.commit()
    return {"status": "success"}


@app.post("/users/{user_id}/mappings")
async def create_song_mapping(
    user_id: str, mapping: SongMappingCreate, db: Session = Depends(get_db)
):
    from uuid import uuid4

    song_mapping = SongMapping(
        id=str(uuid4()),
        user_id=user_id,
        trigger_song_id=mapping.trigger_song_id,
        queue_song_id=mapping.queue_song_id,
    )
    db.add(song_mapping)
    db.commit()
    return {"id": song_mapping.id}


@app.post("/users/{user_id}/queue/current")
async def handle_current_song(
    user_id: str, current_song: CurrentSongRequest, db: Session = Depends(get_db)
):
    try:
        user = db.query(UserToken).filter(UserToken.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        mapping = (
            db.query(SongMapping)
            .filter(
                SongMapping.user_id == user_id, SongMapping.trigger_song_id == current_song.song_id
            )
            .first()
        )

        if mapping:
            sp = spotipy.Spotify(auth=user.access_token)
            sp.add_to_queue(mapping.queue_song_id)
            return {"status": "success", "queued_song": mapping.queue_song_id}

        return {"status": "success", "queued_song": None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/token")
def get_user_token(user_id: str, db: Session = Depends(get_db)):
    user = db.query(UserToken).filter(UserToken.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}/mappings/{mapping_id}")
def delete_song_mapping(user_id: str, mapping_id: str, db: Session = Depends(get_db)):
    mapping = (
        db.query(SongMapping)
        .filter(SongMapping.id == mapping_id, SongMapping.user_id == user_id)
        .first()
    )
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(mapping)
    db.commit()
    return {"status": "success"}


@app.get("/users/{user_id}/mappings")
async def get_user_mappings(user_id: str, db: Session = Depends(get_db)):
    """Get all song mappings for a user"""
    mappings = db.query(SongMapping).filter(SongMapping.user_id == user_id).all()
    return mappings


if __name__ == "__main__":
    # Set up local database URL if not provided in environment
    if not os.getenv("DATABASE_URL"):
        # Using SQLite for local development
        os.environ["DATABASE_URL"] = "sqlite:///./spotify_queue.db"

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Run the FastAPI application using uvicorn
    uvicorn.run(
        "main:app",  # Replace 'main' with your actual file name
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
    )
