import requests
import time
from .config import CLIENT_ID, CLIENT_SECRET, IGDB_TOKEN_URL, IGDB_API_URL

class IGDBClient:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.token_info = self.get_token()

    def get_token(self):
        response = requests.post(
            IGDB_TOKEN_URL,
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            },
        )
        data = response.json()

        # Expiration timestamp
        expires_in = data["expires_in"]
        return {
            "access_token": data["access_token"],
            "expires_at": time.time() + expires_in - 60  # refresh 1 min early
        }

    def ensure_token_valid(self):
        if time.time() >= self.token_info["expires_at"]:
            self.token_info = self.get_token()

    def request(self, endpoint, query):
        self.ensure_token_valid()

        response = requests.post(
            f"{IGDB_API_URL}/{endpoint}",
            data=query,
            headers={
                "Client-ID": self.client_id,
                "Authorization": f"Bearer {self.token_info['access_token']}"
            }
        )

        # If unauthorized → refresh and retry once
        if response.status_code == 401:
            self.token_info = self.get_token()
            response = requests.post(
                f"{IGDB_API_URL}/{endpoint}",
                data=query,
                headers={
                    "Client-ID": self.client_id,
                    "Authorization": f"Bearer {self.token_info['access_token']}"
                }
            )

        response.raise_for_status()
        return response.json()
