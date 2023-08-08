import json
import webbrowser

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify

from constants import CREDENTIALS_PATH



def main():



    # Initialize the Spotify OAuth object
    sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=SCOPE)

    auth_url = sp_oauth.get_authorize_url()
    webbrowser.open(auth_url)

    # Wait for the user to authorize the app and enter the code
    authorization_code = input("Enter the authorization code: ")

    # Exchange authorization code for access token
    token_info = sp_oauth.get_access_token(authorization_code)

    # Extract the access token
    access_token = token_info['access_token']

    # Now you can use the access token to make API requests
    sp = Spotify(auth=access_token)

    # Example: Get the user's saved tracks
    results = sp.add_to_queue(MICRODOSING_URI)


if __name__ == '__main__':
    main()