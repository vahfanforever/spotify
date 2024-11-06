import logging
import os
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

import requests
import uvicorn
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from spotipy.oauth2 import SpotifyOAuth
from sqlalchemy import Column, DateTime, ForeignKey, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Initialize encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY").encode()
cipher_suite = Fernet(ENCRYPTION_KEY)

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
class TokenInfo(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    expires_at: int


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


class SongItem(BaseModel):
    id: str
    name: Optional[str]
    uri: Optional[str]


class SongRelationships(BaseModel):
    songs: List[SongItem]


class AuthStatus(BaseModel):
    authenticated: bool
    token_info: Optional[TokenInfo]


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/spotify_queue")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Create FastAPI app and router
app = FastAPI(title="Spotify Queue API")
api_v1 = APIRouter(prefix="/v1")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add session middleware
SESSION_SECRET = os.getenv("JWT_SECRET", os.urandom(24))
app.add_middleware(
    SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax", https_only=True, max_age=3600
)


def encrypt_token(token: str) -> str:
    return cipher_suite.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    return cipher_suite.decrypt(encrypted_token.encode()).decode()


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Spotify OAuth setup
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope="user-read-playback-state user-modify-playback-state",
        show_dialog=True,
    )


# Session management
def get_session(request: Request) -> dict:
    return request.session


# Auth Endpoints
@api_v1.get("/login")
async def login():
    """Get Spotify authorization URL"""
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return {"auth_url": auth_url}


@api_v1.get("/callback")
async def callback(
    request: Request, code: str = None, error: str = None, db: Session = Depends(get_db)
):
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}?error={error}")

    try:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_access_token(code)
        session = get_session(request)
        session["token_info"] = token_info

        # Get user ID from Spotify
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}
        response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        user_info = response.json()
        user_id = user_info["id"]
        session["user_id"] = user_id

        # Encrypt token before storing
        encrypted_token = encrypt_token(token_info["access_token"])
        user = UserToken(user_id=user_id, access_token=encrypted_token)
        db.merge(user)
        db.commit()

        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard")
    except Exception as e:
        logger.info(f"Exception {e} was thrown.")
        return RedirectResponse(url=f"{FRONTEND_URL}?error=token_error")


@api_v1.get("/auth/status")
async def auth_status(request: Request, db: Session = Depends(get_db)):
    """Check authentication status"""
    session = get_session(request)
    token_info = session.get("token_info")

    if not token_info:
        return AuthStatus(authenticated=False, token_info=None)

    try:
        now = int(datetime.now().timestamp())
        is_expired = token_info["expires_at"] - now < 60

        if is_expired:
            sp_oauth = create_spotify_oauth()
            token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
            session["token_info"] = token_info

            # Update token in database
            user_id = session["user_id"]
            user = UserToken(user_id=user_id, access_token=token_info["access_token"])
            db.merge(user)
            db.commit()

        return AuthStatus(authenticated=True, token_info=TokenInfo(**token_info))

    except Exception as e:
        return AuthStatus(authenticated=False, token_info=None)


@api_v1.get("/search")
async def search_tracks(request: Request, q: str):
    """Search for tracks on Spotify"""
    session = get_session(request)
    token_info = session.get("token_info")

    if not token_info:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}
        response = requests.get(
            f"https://api.spotify.com/v1/search?q={q}&type=track&limit=10", headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Song Relationship Endpoints
@api_v1.post("/songs/relationships")
async def save_song_relationships(
    request: Request, relationships: SongRelationships, db: Session = Depends(get_db)
):
    """Save song relationships"""
    session = get_session(request)
    user_id = session.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Create mappings for consecutive songs
        for i in range(len(relationships.songs) - 1):
            mapping = SongMapping(
                id=str(uuid4()),
                user_id=user_id,
                trigger_song_id=relationships.songs[i].id,
                queue_song_id=relationships.songs[i + 1].id,
            )
            db.add(mapping)

        db.commit()
        return {"message": "Relationships saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1.get("/songs/relationships")
async def get_song_relationships(request: Request, db: Session = Depends(get_db)):
    """Get all song relationships for the current user"""
    session = get_session(request)
    user_id = session.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        mappings = db.query(SongMapping).filter(SongMapping.user_id == user_id).all()
        relationships = {
            mapping.trigger_song_id: SongItem(
                id=mapping.queue_song_id,
                name=None,
                uri=None,
            )
            for mapping in mappings
        }
        return {"relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Update token retrieval to decrypt tokens
@api_v1.get("/users/{user_id}/token")
async def get_user_token(user_id: str, db: Session = Depends(get_db)):
    user = db.query(UserToken).filter(UserToken.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.user_id, "access_token": user.access_token}


@api_v1.get("/users/{user_id}/mappings")
async def get_user_mappings(user_id: str, db: Session = Depends(get_db)):
    mappings = db.query(SongMapping).filter(SongMapping.user_id == user_id).all()
    return mappings


@api_v1.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(UserToken).all()
    return [{"user_id": user.user_id} for user in users]


@api_v1.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}


@api_v1.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include the router in the app
app.include_router(api_v1)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
