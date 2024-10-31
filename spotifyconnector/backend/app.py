import os
from datetime import datetime
from typing import Dict, List, Optional

import requests
from flask import Flask, jsonify, redirect, request, session
from flask_cors import CORS
from pydantic import BaseModel
from spotipy.oauth2 import SpotifyOAuth


# Pydantic Models
class TokenInfo(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    expires_at: int


class UserToken(BaseModel):
    user_id: str
    access_token: str


class SongItem(BaseModel):
    id: str
    name: Optional[str]
    uri: Optional[str]


class SongMappingCreate(BaseModel):
    trigger_song_id: str
    queue_song_id: str


class SongRelationships(BaseModel):
    songs: List[SongItem]


class AuthStatus(BaseModel):
    authenticated: bool
    token_info: Optional[TokenInfo]


# Flask App Setup
app = Flask(__name__)
CORS(
    app,
    supports_credentials=True,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:5173"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": True,
        }
    },
)
app.secret_key = os.urandom(24)
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
)

# Configuration
FASTAPI_SERVICE_URL = "http://localhost:8000"


class Field:
    token_info = "token_info"
    refresh_token = "refresh_token"
    access_token = "access_token"
    user_id = "user_id"


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope="user-read-playback-state user-modify-playback-state",
        show_dialog=True,
    )


@app.route("/api/songs/relationships", methods=["POST"])
def save_song_relationships():
    """Save the relationships between songs"""
    if Field.token_info not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # Validate incoming data with Pydantic
        data = SongRelationships(songs=request.get_json()["songs"])
        user_id = session[Field.user_id]

        # Create mappings for consecutive songs
        for i in range(len(data.songs) - 1):
            mapping = SongMappingCreate(
                trigger_song_id=data.songs[i].id, queue_song_id=data.songs[i + 1].id
            )

            # Forward each mapping to FastAPI service
            response = requests.post(
                f"{FASTAPI_SERVICE_URL}/users/{user_id}/mappings", json=mapping.dict()
            )
            response.raise_for_status()

        return jsonify({"message": "Relationships saved"})

    except Exception as e:
        print(f"Error saving relationships: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/songs/relationships", methods=["GET"])
def get_song_relationships():
    """Get all song relationships"""
    if Field.token_info not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        user_id = session[Field.user_id]
        response = requests.get(f"{FASTAPI_SERVICE_URL}/users/{user_id}/mappings")
        response.raise_for_status()

        # Convert response to Pydantic models for validation
        mappings = response.json()
        relationships = {
            mapping["trigger_song_id"]: SongItem(
                id=mapping["queue_song_id"],
                name=None,  # These could be populated if needed
                uri=None,
            )
            for mapping in mappings
        }

        return jsonify({"relationships": relationships})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/songs/next/<song_id>", methods=["GET"])
def get_next_song(song_id: str):
    """Get the next song in the sequence"""
    if Field.token_info not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        user_id = session[Field.user_id]
        response = requests.get(f"{FASTAPI_SERVICE_URL}/users/{user_id}/mappings")
        response.raise_for_status()

        mappings = response.json()
        next_song = next(
            (
                mapping["queue_song_id"]
                for mapping in mappings
                if mapping["trigger_song_id"] == song_id
            ),
            None,
        )

        return jsonify({"next_song_id": next_song})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search", methods=["GET"])
def search_tracks():
    """Search for tracks on Spotify"""
    if Field.token_info not in session:
        return jsonify({"error": "Not authenticated"}), 401

    query = request.args.get("q")
    if not query:
        return jsonify({"error": "No search query provided"}), 400

    try:
        token_info = TokenInfo(**session[Field.token_info])
        sp_oauth = create_spotify_oauth()

        # Check if token needs refresh
        now = int(datetime.now().timestamp())
        is_expired = token_info.expires_at - now < 60

        if is_expired:
            new_token_info = sp_oauth.refresh_access_token(token_info.refresh_token)
            token_info = TokenInfo(**new_token_info)
            session[Field.token_info] = token_info.dict()

        headers = {"Authorization": f"Bearer {token_info.access_token}"}
        response = requests.get(
            f"https://api.spotify.com/v1/search?q={query}&type=track&limit=10", headers=headers
        )
        response.raise_for_status()
        return jsonify(response.json())

    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/login")
def login():
    """Get Spotify authorization URL"""
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return jsonify({"auth_url": auth_url})


@app.route("/callback")
def callback():
    """Handle Spotify OAuth callback"""
    sp_oauth = create_spotify_oauth()
    error = request.args.get("error")
    if error:
        print(f"Error in callback: {error}")
        return redirect(f"http://localhost:5173?error={error}")

    code = request.args.get("code")

    try:
        token_info = TokenInfo(**sp_oauth.get_access_token(code))
        session[Field.token_info] = token_info.dict()

        # Get user ID from Spotify
        headers = {"Authorization": f"Bearer {token_info.access_token}"}
        response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        user_info = response.json()
        user_id = user_info["id"]
        session[Field.user_id] = user_id

        # Check if user exists
        check_user_response = requests.get(f"{FASTAPI_SERVICE_URL}/users/{user_id}/token")

        if check_user_response.status_code == 404:
            # User doesn't exist, create new user
            user_token = UserToken(user_id=user_id, access_token=token_info.access_token)
            response = requests.post(f"{FASTAPI_SERVICE_URL}/users/token", json=user_token.dict())
        else:
            # User exists, update token
            user_token = UserToken(user_id=user_id, access_token=token_info.access_token)
            response = requests.put(
                f"{FASTAPI_SERVICE_URL}/users/{user_id}/token", json=user_token.dict()
            )

        response.raise_for_status()
        return redirect("http://localhost:5173/dashboard")
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        return redirect("http://localhost:5173?error=token_error")


@app.route("/api/auth/status")
def auth_status():
    """Check if user is authenticated"""
    if Field.token_info not in session:
        return jsonify(AuthStatus(authenticated=False, token_info=None).dict())

    try:
        token_info = TokenInfo(**session[Field.token_info])
        now = int(datetime.now().timestamp())
        is_expired = token_info.expires_at - now < 60

        if is_expired:
            sp_oauth = create_spotify_oauth()
            new_token_info = sp_oauth.refresh_access_token(token_info.refresh_token)
            token_info = TokenInfo(**new_token_info)
            session[Field.token_info] = token_info.dict()

            # Update token in FastAPI service
            user_id = session[Field.user_id]

            # Always use PUT for token updates in auth status
            # since we know the user exists at this point
            user_token = UserToken(user_id=user_id, access_token=token_info.access_token)
            response = requests.put(
                f"{FASTAPI_SERVICE_URL}/users/{user_id}/token", json=user_token.dict()
            )
            response.raise_for_status()

        auth_status = AuthStatus(authenticated=True, token_info=token_info)
        return jsonify(auth_status.dict())

    except Exception as e:
        print(f"Error in auth status: {str(e)}")
        return jsonify(AuthStatus(authenticated=False, token_info=None).dict())


@app.route("/api/logout")
def logout():
    """Clear session and logout"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
