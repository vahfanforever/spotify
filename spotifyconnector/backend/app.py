import os
from datetime import datetime
from typing import Dict

import requests
from flask import Flask, jsonify, redirect, request, session
from flask_cors import CORS
from spotipy.oauth2 import SpotifyOAuth

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
app.secret_key = os.urandom(24)  # Make this a fixed value during development
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
)


class Field:
    token_info = "token_info"
    refresh_token = "refresh_token"
    access_token = "access_token"


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope="user-read-playback-state user-modify-playback-state",
        show_dialog=True,  # might not need this
    )


song_relationships: Dict[str, str] = {}


@app.route("/api/songs/relationships", methods=["POST"])
def save_song_relationships():
    """Save the relationships between songs"""
    if Field.token_info not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        data = request.get_json()
        songs = data.get("songs", [])

        # Clear existing relationships for this user
        # In a real app, you'd scope this to the user
        global song_relationships
        song_relationships.clear()

        # Save relationships between consecutive songs
        for i in range(len(songs) - 1):
            current_song = songs[i]["id"]
            next_song = songs[i + 1]["id"]
            song_relationships[current_song] = next_song

        return jsonify({"message": "Relationships saved", "relationships": song_relationships})

    except Exception as e:
        print(f"Error saving relationships: {str(e)}")
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
        token_info = session[Field.token_info]
        sp_oauth = create_spotify_oauth()

        # Check if token needs refresh
        now = int(datetime.now().timestamp())
        is_expired = token_info["expires_at"] - now < 60

        if is_expired:
            token_info = sp_oauth.refresh_access_token(token_info[Field.refresh_token])
            session[Field.token_info] = token_info

        headers = {"Authorization": f"Bearer {token_info[Field.access_token]}"}

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
        print(f"Error in callback: {error}")  # Add logging
        return redirect(f"http://localhost:5173?error={error}")

    code = request.args.get("code")

    try:
        token_info = sp_oauth.get_access_token(code)
        session[Field.token_info] = token_info
        return redirect("http://localhost:5173/dashboard")
    except Exception as e:
        print(f"Error getting token: {str(e)}")  # Add logging
        return redirect("http://localhost:5173?error=token_error")


@app.route("/api/auth/status")
def auth_status():
    """Check if user is authenticated"""
    if Field.token_info not in session:
        return jsonify({"authenticated": False})

    token_info = session[Field.token_info]
    now = int(datetime.now().timestamp())
    is_expired = token_info["expires_at"] - now < 60

    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info[Field.refresh_token])
        session[Field.token_info] = token_info

    return jsonify(
        {
            "authenticated": True,
            "token_info": {
                "access_token": token_info[Field.access_token],
                "expires_at": token_info["expires_at"],
            },
        }
    )


@app.route("/api/logout")
def logout():
    """Clear session and logout"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
