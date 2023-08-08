from dataclasses import dataclass
import json

CREDENTIALS_PATH = r"C:\Users\user\source\spotify\credentials.json"
SCOPE = 'user-modify-playback-state'
MICRODOSING_URI = "24yb4Wz0iBvBNOaIW2dVOD"

@dataclass
class Credentials:
    id: str
    secret: str
    redirect_uri: str

def get_credentials():
    with open(CREDENTIALS_PATH, 'r') as json_file:
        credentials = json.loads(json_file.read())

    return Credentials(
        id=credentials["id"],
        secret=credentials["secret"],
        redirect_uri=credentials["uri"]
    )