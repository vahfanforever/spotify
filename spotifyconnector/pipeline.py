from typing import Dict
from pydantic import BaseModel

from constants import (
    SpotifyScopes,
    CREDENTIALS_PATH,
    TEST_SONGS_TO_CONNECT,
    SpotifyAccess,
)
from spotify_api import (
    get_spotify_access,
    check_if_user_is_active,
    get_current_songs_uri,
    add_song_to_queue,
)


class SpotifyConnectorConfig(BaseModel):
    spotify_access: SpotifyAccess
    connecting_songs: Dict[str, str]


def connect_songs(config: SpotifyConnectorConfig):
    spotify = get_spotify_access(config.spotify_access)
    if check_if_user_is_active(spotify):
        current_uri = get_current_songs_uri(spotify)
        for playing, to_play in config.connecting_songs.items():
            if playing == current_uri:
                add_song_to_queue(spotify, to_play)
                print("added to queue woop")
                return

        print("songs are playing but not the right ones :/")
    else:
        print("go on spotify ya cunt")


if __name__ == "__main__":
    config = SpotifyConnectorConfig(
        spotify_access=SpotifyAccess(
            credentials_path=CREDENTIALS_PATH, scope=SpotifyScopes.ADD_SONG_TO_QUEUE
        ),
        connecting_songs=TEST_SONGS_TO_CONNECT,
    )
    connect_songs(config)
