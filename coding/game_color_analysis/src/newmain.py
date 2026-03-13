import csv
import os
import requests
import numpy as np
import pandas as pd
import colorsys
from PIL import Image
from sklearn.cluster import KMeans

# --- CONFIG ---
CLIENT_ID = "YOUR_CLIENT_ID"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
URL = "https://api.igdb.com/v4/games"

START_YEAR = 2016
END_YEAR = 2025
MAX_SCREENSHOTS_PER_GAME = 5

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SCREENSHOT_DIR = os.path.join(DATA_DIR, "screenshots")
OUTPUT_CSV = os.path.join(DATA_DIR, "game_data.csv")

HEADERS = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {ACCESS_TOKEN}"}
NSFW_WORDS = ["erotica", "hentai", "nsfw", "nudity", "sexual content", "adult", "pornographic"]


def get_palette_and_metrics(image_path, n_clusters=5):
    """Extracts weighted colors and calculates HSV/Luminance metrics."""
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            # For Metrics: Use slightly higher res for better accuracy
            metrics_img = img.resize((100, 100))
            pixels_metrics = np.array(metrics_img).reshape(-1, 3) / 255.0

            # Calculate Avg Saturation and Luminance (Your logic)
            sats = []
            lums = []
            for r, g, b in pixels_metrics:
                _, s, _ = colorsys.rgb_to_hsv(r, g, b)
                lum = 0.299 * r * 255 + 0.587 * g * 255 + 0.114 * b * 255
                sats.append(s)
                lums.append(lum)

            avg_sat = np.mean(sats)
            avg_lum = np.mean(lums)

            # For Palette: Use small res for speed
            pal_img = img.resize((50, 50))
            pixels_pal = np.array(pal_img).reshape(-1, 3)

        kmeans = KMeans(n_clusters=n_clusters, n_init=1, max_iter=10, random_state=42).fit(
            pixels_pal
        )
        colors = kmeans.cluster_centers_
        labels = kmeans.labels_
        weights = np.bincount(labels) / len(labels)

        palette = []
        for i in range(len(colors)):
            palette.append((*map(int, colors[i]), float(weights[i])))

        palette.sort(key=lambda x: x[3], reverse=True)
        return palette, avg_sat, avg_lum
    except Exception as e:
        print(f"[ERROR] Image processing failed: {e}")
        return [], 0, 0


def query_igdb(year, offset=0):
    query = f"""
    fields name, release_dates.y, screenshots.url, genres.name, 
           themes.name, keywords.name, player_perspectives.name,
           involved_companies.developer, involved_companies.company.name;
    where release_dates.y = {year} & screenshots != null;
    limit 500; offset {offset};
    """
    try:
        response = requests.post(URL, headers=HEADERS, data=query, timeout=15)
        return response.json()
    except:
        return []


def download_image(url):
    if not url:
        return None
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    if url.startswith("//"):
        url = "https:" + url
    img_url = url.replace("t_thumb", "t_screenshot_big")
    filename = os.path.join(SCREENSHOT_DIR, img_url.split("/")[-1])
    if os.path.exists(filename):
        return filename
    try:
        r = requests.get(img_url, timeout=15)
        with open(filename, "wb") as f:
            f.write(r.content)
        return filename
    except:
        return None


def main():
    color_headers = []
    for i in range(1, 6):
        color_headers.extend([f"C{i}_R", f"C{i}_G", f"C{i}_B", f"C{i}_W"])

    header = [
        "Year",
        "Decade",
        "Game",
        "Screenshot",
        "Genres",
        "Themes",
        "Keywords",
        "Perspectives",
        "Developers",
        "Is_NSFW",
        "Avg_Saturation",
        "Avg_Luminance",
    ] + color_headers

    if not os.path.exists(OUTPUT_CSV):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)
        processed = set()
    else:
        df_existing = pd.read_csv(OUTPUT_CSV)
        processed = set(df_existing["Screenshot"].astype(str).tolist())

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for year in range(START_YEAR, END_YEAR + 1):
            offset = 0
            while True:
                games = query_igdb(year, offset)
                if not games:
                    break
                for game in games:
                    name = game.get("name", "Unknown")
                    genres = "|".join(g["name"] for g in game.get("genres", []))
                    themes = "|".join(t["name"] for t in game.get("themes", []))
                    keywords = "|".join(k["name"] for k in game.get("keywords", []))
                    perspectives = "|".join(p["name"] for p in game.get("player_perspectives", []))
                    devs = "|".join(
                        c["company"]["name"]
                        for c in game.get("involved_companies", [])
                        if c.get("developer")
                    )

                    combined_text = f"{genres} {themes} {keywords} {name}".lower()
                    is_nsfw = 1 if any(word in combined_text for word in NSFW_WORDS) else 0

                    for screen in game.get("screenshots", [])[:MAX_SCREENSHOTS_PER_GAME]:
                        img_path = download_image(screen["url"])
                        if not img_path or img_path in processed:
                            continue

                        palette, sat, lum = get_palette_and_metrics(img_path)
                        color_row = []
                        for i in range(5):
                            if i < len(palette):
                                color_row.extend(list(palette[i]))
                            else:
                                color_row.extend([None, None, None, 0.0])

                        writer.writerow(
                            [
                                year,
                                year // 10 * 10,
                                name,
                                img_path,
                                genres,
                                themes,
                                keywords,
                                perspectives,
                                devs,
                                is_nsfw,
                                sat,
                                lum,
                            ]
                            + color_row
                        )
                        processed.add(img_path)
                    print(f"Processed: {name}")
                offset += len(games)


if __name__ == "__main__":
    main()
