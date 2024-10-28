from flask import Flask, redirect, request, session, url_for
from spotipy.oauth2 import SpotifyOAuth
import os
from datetime import datetime

app = Flask(__name__)

# Need a secret key for session handling
app.secret_key = os.urandom(24) 

class Field:
    token_info = "token_info"
    refresh_token = "refresh_token"
    access_token = "access_token"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),  # Must match Spotify dashboard
        scope="user-read-playback-state user-modify-playback-state"
    )

@app.route('/')
def index():
    """Welcome page for users to login."""
    return "Welcome! <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
    """Spotify login options."""
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handles authentication."""
    sp_oauth = create_spotify_oauth()
    error = request.args.get('error')
    if error:
        return f"Error: {error}"
    
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    
    # Save token info in session
    session[Field.token_info] = token_info
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if Field.token_info not in session:
        return redirect('/login')
        
    token_info = session[Field.token_info]
    now = int(datetime.now().timestamp())
    is_expired = token_info['expires_at'] - now < 60
    
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info[Field.refresh_token])
        session[Field.token_info] = token_info
    
    return f"""
        <h1>Successfully logged in!</h1>
        <p>Access Token: {token_info[Field.access_token][:50]}...</p>
        <p>Expires at: {datetime.fromtimestamp(token_info['expires_at'])}</p>
        <p><a href="/logout">Logout</a></p>
    """

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)