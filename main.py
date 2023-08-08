import json
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify

CREDENTIALS_PATH = r"C:\Users\user\source\spotify\credentials.json"

def main():

    with open(CREDENTIALS_PATH, 'r') as json_file:
        credentials = json.loads(json_file.read())

    # Set your Spotify API credentials
    client_id = credentials["id"]
    client_secret = credentials["secret"]
    redirect_uri = credentials["uri"]

    # Initialize the Spotify OAuth object
    sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope='user-library-read')

    auth_url = sp_oauth.get_authorize_url()
    print(f"Please authorize the app by visiting: {auth_url}")

    # Wait for the user to authorize the app and enter the code
    authorization_code = input("Enter the authorization code: ")

    # Exchange authorization code for access token
    token_info = sp_oauth.get_access_token(authorization_code)

    # Extract the access token
    access_token = token_info['access_token']

    # Now you can use the access token to make API requests
    sp = Spotify(auth=access_token)
    # # Obtain user's authorization token
    # auth_token = sp_oauth.get_access_token(as_dict=False)

    # # Initialize the Spotipy object with the obtained token
    # sp = Spotify(auth=auth_token)

    # Example: Get the user's saved tracks
    results = sp.current_user_saved_tracks()
    for idx, item in enumerate(results['items']):
        track = item['track']
        print(f"{idx + 1}. {track['name']} - {', '.join([artist['name'] for artist in track['artists']])}")


if __name__ == '__main__':
    main()