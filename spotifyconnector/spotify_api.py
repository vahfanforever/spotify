import webbrowser

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify

from spotifyconnector.constants import get_credentials, SpotifyAccess
from spotifyconnector.scraper import scrape_uri_webpage


def get_spotify_oauth(credentials_path: str, scope: str):
    credentials = get_credentials(credentials_path)
    return SpotifyOAuth(
        client_id=credentials.id,
        client_secret=credentials.secret,
        redirect_uri=credentials.redirect_uri,
        scope=scope,
    )


def get_spotify_access(spotify_access: SpotifyAccess, scrape: bool = True) -> Spotify:
    sp_oauth = get_spotify_oauth(
        spotify_access.credentials_path, spotify_access.scope.value
    )
    auth_url = sp_oauth.get_authorize_url()

    if scrape:
        authorization_code = scrape_uri_webpage(auth_url)
    else:
        # access webpage instead (user interaction)
        webbrowser.open(auth_url)
        authorization_code = input("Enter the authorization code: ")

    token_info = sp_oauth.get_access_token(authorization_code)
    access_token = token_info["access_token"]

    return Spotify(auth=access_token)


def check_if_user_is_active(sp: Spotify) -> bool:
    return bool(sp.current_playback())


def get_current_songs_uri(sp: Spotify) -> str:
    current_playback = sp.current_playback()
    uri = current_playback["item"]["uri"]
    return uri.split("spotify:track:")[1]


def add_song_to_queue(sp: Spotify, song_uri: str):
    sp.add_to_queue(song_uri)
