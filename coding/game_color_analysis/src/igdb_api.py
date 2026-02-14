"""IGDB API interaction and image downloading."""

import os

import requests

# IGDB API credentials
CLIENT_ID = "6k1gmqbtqyihlzrqijshniy5fs3xis"
ACCESS_TOKEN = "29k238k6a623u6utzjoomusny7wzrv"
URL = "https://api.igdb.com/v4/games"

# delete?
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SCREENSHOT_DIR = os.path.join(DATA_DIR, "screenshots")

HEADERS = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {ACCESS_TOKEN}"}


def query_igdb(year, limit=500, offset=0):
    """
    Query games released in a given year. Download screenshots.
    Using pagination to fetch all available games.
    Returns a dictionary of games, empty list on failure.
    year: int - release year to query
    limit: int - batchsize from IGDB (default 500)
    offset: int - pagination offset
    """
    query = f"""
    fields release_dates.y, name, screenshots.url, genres.name, themes.name;
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
    """Download a screenshot from IGDB URL, only if it doesn’t already exist.
    Returns the local file path or None."""

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
