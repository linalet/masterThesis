"""Main script to fetch game data and analyze color palettes from screenshots."""

import csv
import os
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.cluster import KMeans

from igdb_api import download_image, query_igdb


# Analysis settings
START_YEAR = 1980
# 1950  # Tennis for two 1958? OXO 1952?
END_YEAR = 2025
MAX_SCREENSHOTS_PER_GAME = 5  # possibly increase to 10

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "game_data.csv")


def get_palette(image_path, n_clusters=5):
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        # Make img smaller for fast processing -> colors not details
        img = img.resize((50, 50))
        # matrix to array for KMeans
        pixels = np.array(img).reshape(-1, 3)

    kmeans = KMeans(n_clusters=n_clusters, n_init=1, max_iter=10, random_state=42).fit(pixels)
    raw_colors = kmeans.cluster_centers_

    palette = []
    for color in raw_colors:
        r, g, b = map(int, color)

        # Grey correction for B&W images
        if abs(r - g) < 10 and abs(r - b) < 10 and abs(g - b) < 10:
            avg = (r + g + b) // 3
            r, g, b = avg, avg, avg

        # Merge blacks and whites
        if r < 35 and g < 35 and b < 35:
            r, g, b = 0, 0, 0
        if r > 220 and g > 220 and b > 220:
            r, g, b = 255, 255, 255

        # Merge similar colors (quantization)
        r, g, b = (round(x / 10) * 10 for x in (r, g, b))
        palette.append((r, g, b))

    return list(set(palette))


def main():
    # Prepare CSV
    color_headers = []
    for i in range(1, 6):
        color_headers.extend([f"C{i}_R", f"C{i}_G", f"C{i}_B"])
    header = [
        "Year",
        "Decade",
        "Game",
        "Screenshot",
        "Genres",
        "Themes",
        "Keywords",
        "Player Perspectives",
        "Developers",
    ] + color_headers

    if os.path.exists(OUTPUT_CSV):
        # Load existing rows to skip duplicates
        current_csv = pd.read_csv(OUTPUT_CSV)
        processed = set(current_csv["Screenshot"].astype(str).tolist())
    else:
        # Create new CSV with header
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(header)
        processed = set()

    # Open CSV in append mode
    with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        for year in range(START_YEAR, END_YEAR + 1):
            print(f"[INFO] Getting games from {year}...")
            offset = 0
            while True:
                games = query_igdb(year, offset=offset)
                if not games:
                    break  # no more games

                for game in games:
                    name = game.get("name", "Unknown")

                    companies = game.get("involved_companies", [])
                    devs = "|".join([c["company"]["name"] for c in companies if c.get("developer")])
                    genres = "|".join(g["name"] for g in game.get("genres", []) if "name" in g)
                    themes = "|".join(t["name"] for t in game.get("themes", []) if "name" in t)
                    keywords = "|".join(k["name"] for k in game.get("keywords", []) if "name" in k)
                    perspectives = "|".join(
                        p["name"] for p in game.get("player_perspectives", []) if "name" in p
                    )
                    screenshots = game.get("screenshots", [])

                    for screen in screenshots[:MAX_SCREENSHOTS_PER_GAME]:
                        image_path = download_image(screen["url"])
                        # Skip if download failed or already recorded
                        if not image_path or image_path in processed:
                            continue

                        # Get palette
                        palette = get_palette(image_path, n_clusters=5)
                        color_data = []
                        for i in range(5):
                            if i < len(palette):
                                r, g, b = palette[i]
                                color_data.extend([r, g, b])
                            else:
                                color_data.extend([None, None, None])
                        # Write row
                        writer.writerow(
                            [
                                year,
                                year // 10 * 10,
                                name,
                                image_path,
                                genres,
                                themes,
                                keywords,
                                perspectives,
                                devs,
                            ]
                            + color_data
                        )
                        processed.add(image_path)
                        print(f"[INFO] Saved {name} ({year})")

                offset += len(games)
            print(f"[INFO] Finished all games for {year}")

    print("[INFO] Data collection complete!")


if __name__ == "__main__":
    main()
