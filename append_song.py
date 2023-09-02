import json
import webbrowser

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify

from constants import MICRODOSING_URI, get_credentials, SCOPE
from scrape import scrape



def main():

    credentials = get_credentials()

    # Initialize the Spotify OAuth object
    sp_oauth = SpotifyOAuth(client_id=credentials.id, client_secret=credentials.secret, redirect_uri=credentials.redirect_uri, scope="user-read-playback-state")

    auth_url = sp_oauth.get_authorize_url()
    authorization_code = scrape(auth_url)

    # access webpage instead (user interaction)
    webbrowser.open(auth_url)
    authorization_code = input("Enter the authorization code: ")

    # Exchange authorization code for access token
    token_info = sp_oauth.get_access_token(authorization_code)

    # Extract the access token
    access_token = token_info['access_token']

    # Now you can use the access token to make API requests
    sp = Spotify(auth=access_token)


    # need to check if the user is active
    current_playback = sp.current_playback()

    if not current_playback:
        print("here")

    # check the current song

    # loop through dictionary of song pairings

    # add to queue a song if there's a match
    sp.add_to_queue(MICRODOSING_URI)

if __name__ == '__main__':
    main()