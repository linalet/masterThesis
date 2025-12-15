"""IGDB API interaction and image downloading."""

import os

import requests
from config import URL, ACCESS_TOKEN, BATCH_SIZE, CLIENT_ID, SCREENSHOT_DIR

HEADERS = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {ACCESS_TOKEN}"}


def query_igdb(year, limit=BATCH_SIZE, offset=0):
    """
    Query games released in a given year. Download screenshots.
    Using pagination to fetch all available games.
    Returns an empty list on failure, list of game dicts on success.
    """
    query = f"""
    fields name, release_dates.y, screenshots.url;
    where release_dates.y = {year} & screenshots != null;
    limit {limit};
    offset {offset};
    """
    try:
        response = requests.post(URL, headers=HEADERS, data=query, timeout=15)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch games for {year} (offset {offset}): {e}")
        return []


def normalize_igdb_url(url):
    """Normalize IGDB image URLs to ensure they are valid. IGDB changed URL format :( )."""

    url = url.strip()

    while url.startswith("https://https://"):
        url = url.replace("https://https://", "https://")

    if url.startswith("//"):
        url = "https:" + url

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url.lstrip("/")

    return url


def download_image(url, folder=SCREENSHOT_DIR):
    """Download a screenshot from IGDB URL if it doesn’t already exist.
    Returns the local file path or None on failure."""

    os.makedirs(folder, exist_ok=True)

    url = normalize_igdb_url(url)
    img_url = url.replace("t_thumb", "t_screenshot_big")
    filename = os.path.join(folder, img_url.split("/")[-1])

    # Skip download if already exists
    if os.path.exists(filename):
        return filename

    try:
        img_data = requests.get(img_url, timeout=15)
        img_data.raise_for_status()

        with open(filename, "wb") as f:
            f.write(img_data.content)

        return filename

    except requests.RequestException as e:
        print(f"[ERROR] Failed to download image {url}: {e}")
        return None
