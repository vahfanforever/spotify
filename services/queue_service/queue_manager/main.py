import logging
import os
import time

import requests
import spotipy

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class QueueManager:
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url
        self.active_users = set()
        self.user_last_check = {}
        self.check_interval = 30  # seconds between checks for each user

    def get_all_users(self):
        """Fetch all users from the FastAPI service"""
        try:
            response = requests.get(f"{self.api_base_url}/users")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching users: {str(e)}")
            return []

    def get_user_token(self, user_id):
        """Get user's token from the FastAPI service"""
        try:
            response = requests.get(f"{self.api_base_url}/users/{user_id}/token")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching user token: {str(e)}")
            return None

    def get_user_mappings(self, user_id):
        """Fetch all song mappings for a user from the FastAPI service"""
        try:
            response = requests.get(f"{self.api_base_url}/users/{user_id}/mappings")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching user mappings: {str(e)}")
            return []

    def check_user_active(self, sp):
        """Check if user has an active Spotify session"""
        try:
            playback = sp.current_playback()
            return playback is not None
        except Exception as e:
            logger.error(f"Error checking user activity: {str(e)}")
            return False

    def get_current_track(self, sp):
        """Get the current track ID and next track in queue"""
        try:
            playback = sp.current_playback()
            if not playback or not playback["item"]:
                return None, None

            current_track_id = playback["item"]["id"]

            # Get the next track in queue
            queue = sp.queue()
            next_track = queue["queue"][0] if queue and queue["queue"] else None
            next_track_id = next_track["id"] if next_track else None

            return current_track_id, next_track_id
        except Exception as e:
            logger.error(f"Error getting current track: {str(e)}")
            return None, None

    def find_mapping_for_track(self, track_id, mappings):
        """Find if there's a mapping for the given track"""
        for mapping in mappings:
            if mapping["trigger_song_id"] == track_id:
                return mapping
        return None

    def process_user(self, user):
        """Process a single user's queue"""
        user_id = user["user_id"]

        try:
            # Get user's access token
            user_token = self.get_user_token(user_id)
            if not user_token:
                logger.error(f"Could not get token for user {user_id}")
                return

            # Initialize Spotify client
            sp = spotipy.Spotify(auth=user_token["access_token"])

            # Check if user is active
            if not self.check_user_active(sp):
                if user_id in self.active_users:
                    logger.info(f"User {user_id} became inactive")
                    self.active_users.remove(user_id)
                return

            # Mark user as active
            if user_id not in self.active_users:
                logger.info(f"User {user_id} became active")
                self.active_users.add(user_id)

            # Get current track and next track in queue
            current_track_id, next_track_id = self.get_current_track(sp)
            if not current_track_id:
                return

            # Get user's mappings and check if current track has a mapping
            mappings = self.get_user_mappings(user_id)
            mapping = self.find_mapping_for_track(current_track_id, mappings)

            if mapping:
                # If we found a mapping and either there's no next track
                # or the next track isn't the mapped song, queue it
                mapped_song_id = mapping["queue_song_id"]
                if not next_track_id or next_track_id != mapped_song_id:
                    try:
                        sp.add_to_queue(f"spotify:track:{mapped_song_id}")
                        logger.info(
                            f"Added mapped song {mapped_song_id} to queue for user {user_id} "
                            f"(triggered by {current_track_id})"
                        )
                    except Exception as e:
                        logger.error(f"Error adding song to queue: {str(e)}")

        except Exception as e:
            logger.error(f"Error processing user {user_id}: {str(e)}")
            if user_id in self.active_users:
                self.active_users.remove(user_id)

    def run(self):
        """Main loop to continuously check users and manage queues"""
        logger.info("Starting Spotify Queue Manager")

        while True:
            try:
                users = self.get_all_users()
                current_time = time.time()

                for user in users:
                    # Check if enough time has passed since last check for this user
                    if (
                        current_time - self.user_last_check.get(user["user_id"], 0)
                        >= self.check_interval
                    ):
                        self.process_user(user)
                        self.user_last_check[user["user_id"]] = current_time

                # Short sleep to prevent excessive CPU usage
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(5)


if __name__ == "__main__":
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    queue_manager = QueueManager(api_base_url)
    queue_manager.run()
