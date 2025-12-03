import os
import requests
import csv
from colorthief import ColorThief
import io
from PIL import Image

# =============================
# CONFIG
# =============================

CLIENT_ID = "6k1gmqbtqyihlzrqijshniy5fs3xis"
ACCESS_TOKEN = "9y11k23ahyaogrjirm5l8awefat61x"

START_YEAR = 2000
END_YEAR = 2005
OUTPUT_FOLDER = "screenshots"
OUTPUT_CSV = "game_color_palettes.csv"

# =============================
# IGDB API SETUP
# =============================

HEADERS = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def query_igdb(year, limit=5):
    """Query IGDB for games released in a given year with screenshots."""
    query = f"""
    fields name, release_dates.y, screenshots.url;
    where release_dates.y = {year} & screenshots != null;
    limit {limit};
    """
    url = "https://api.igdb.com/v4/games"
    response = requests.post(url, headers=HEADERS, data=query)
    response.raise_for_status()
    return response.json()

def download_image(url, folder=OUTPUT_FOLDER):
    """Download screenshot from IGDB URL."""
    os.makedirs(folder, exist_ok=True)
    img_url = "https:" + url.replace("t_thumb", "t_screenshot_big")
    filename = os.path.join(folder, img_url.split("/")[-1])
    img_data = requests.get(img_url).content
    with open(filename, "wb") as f:
        f.write(img_data)
    return filename

def extract_palette(image_path, color_count=6):
    """Extract dominant color palette from an image."""
    try:
        ct = ColorThief(image_path)
        palette = ct.get_palette(color_count=color_count)
        return palette
    except Exception as e:
        print(f"Palette extraction failed for {image_path}: {e}")
        return []

# =============================
# MAIN LOOP
# =============================

with open(OUTPUT_CSV, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Year", "Game", "Screenshot", "Palette"])  # header row

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Fetching games from {year}...")
        try:
            games = query_igdb(year, limit=5)
        except Exception as e:
            print(f"Failed to fetch {year}: {e}")
            continue

        for game in games:
            name = game.get("name", "Unknown")
            screenshots = game.get("screenshots", [])

            for sc in screenshots[:2]:  # only take 2 screenshots per game
                try:
                    img_path = download_image(sc["url"])
                    palette = extract_palette(img_path)
                    writer.writerow([year, name, img_path, palette])
                    print(f"Saved {name} ({year}) with palette {palette}")
                except Exception as e:
                    print(f"Error processing screenshot: {e}")
