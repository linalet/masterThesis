import requests

CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"

url = "https://id.twitch.tv/oauth2/token"
params = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "client_credentials"
}

response = requests.post(url, params=params)
data = response.json()

print("Access Token:", data["access_token"])
print("Expires in (seconds):", data["expires_in"])
