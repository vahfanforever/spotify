from dataclasses import dataclass
import json
from enum import Enum

CREDENTIALS_PATH = r"C:\Users\user\source\spotify\credentials.json"
URL = "http://127.0.0.1:5000/"
MICRODOSING_URI = "24yb4Wz0iBvBNOaIW2dVOD"
TEST_SONGS_TO_CONNECT = {MICRODOSING_URI: MICRODOSING_URI}


@dataclass
class Credentials:
    id: str
    secret: str
    redirect_uri: str


def get_credentials(credentials: str) -> Credentials:
    with open(credentials, "r") as json_file:
        credentials = json.loads(json_file.read())

    return Credentials(
        id=credentials["id"],
        secret=credentials["secret"],
        redirect_uri=credentials["uri"],
    )


# scopes needed to perform a particular task
class SpotifyScopes(Enum):
    ADD_SONG_TO_QUEUE = "user-modify-playback-state user-read-playback-state"