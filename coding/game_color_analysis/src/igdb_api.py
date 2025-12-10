import os
import requests
from urllib.parse import urlparse
from config import CLIENT_ID, ACCESS_TOKEN, SCREENSHOT_DIR, BATCH_SIZE

HEADERS = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def query_igdb(year, limit=BATCH_SIZE, offset=0):
    """
    Query games released in a given year with screenshots.
    Uses pagination (offset) to fetch all available games.
    """
    query = f"""
    fields name, release_dates.y, screenshots.url;
    where release_dates.y = {year} & screenshots != null;
    limit {limit};
    offset {offset};
    """
    url = "https://api.igdb.com/v4/games"
    try:
        response = requests.post(url, headers=HEADERS, data=query, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        print(f"[ERROR] Failed to fetch games for {year} (offset {offset}): {e}")
        return []
    except requests.RequestException as e:
        print(f"[ERROR] Request exception for {year} (offset {offset}): {e}")
        return []
    
def normalize_igdb_url(url: str) -> str:
    """Normalize IGDB image URLs to ensure they are valid."""

    url = url.strip()

    # Remove extra "https://"
    while url.startswith("https://https://"):
        url = url.replace("https://https://", "https://")

    
    if url.startswith("//"):
        url = "https:" + url

    # If url has no scheme at all, add https://
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url.lstrip("/")

    return url

def download_image(url, folder=SCREENSHOT_DIR):
    """Download a screenshot from IGDB URL if it doesn’t already exist."""
    os.makedirs(folder, exist_ok=True)
    try:
        # Normalize the URL (IGDB changed URL format :/ )
        url = normalize_igdb_url(url)

        img_url = url.replace("t_thumb", "t_screenshot_big")
        
        filename = os.path.join(folder, img_url.split("/")[-1])
        
        # Skip download if already exists
        if os.path.exists(filename):
            return filename
        
        img_data = requests.get(img_url, timeout=15)
        img_data.raise_for_status()

        with open(filename, "wb") as f:
            f.write(img_data.content)

        return filename
    
    except Exception as e:
        print(f"[ERROR] Failed to download image {url}: {e}")
        return None

