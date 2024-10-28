import webbrowser

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify


def check_if_user_is_active(sp: Spotify) -> bool:
    return bool(sp.current_playback())


def get_current_songs_uri(sp: Spotify) -> str:
    current_playback = sp.current_playback()
    uri = current_playback["item"]["uri"]
    return uri.split("spotify:track:")[1]


def add_song_to_queue(sp: Spotify, song_uri: str):
    sp.add_to_queue(song_uri)
