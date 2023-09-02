import sys

print(sys.path)

from typing import Dict
from pydantic import BaseModel

from constants import (
    SpotifyScopes,
    CREDENTIALS_PATH,
    TEST_SONGS_TO_CONNECT,
)
from spotify_api import (
    get_spotify_access,
    get_spotify_oauth,
    check_if_user_is_active,
    add_song_to_queue,
)


class SpotifyConnectorConfig(BaseModel):
    credentials_path: str
    scope: SpotifyScopes
    connecting_songs: Dict[str, str]


def connect_songs(config: SpotifyConnectorConfig):
    oauth = get_spotify_oauth(config.credentials_path, config.scope.value)
    spotify = get_spotify_access(oauth)
    if check_if_user_is_active(spotify):
        print("WOOOO")
        # for playing, to_play in config.connecting_songs.items():
    else:
        print("go on spotify ya cunt")


if __name__ == "__main__":
    config = SpotifyConnectorConfig(
        credentials_path=CREDENTIALS_PATH,
        scope=SpotifyScopes.ADD_SONG_TO_QUEUE,
        connecting_songs=TEST_SONGS_TO_CONNECT,
    )
    connect_songs(config)
