"""Main script to fetch game data and analyze color palettes from screenshots."""

import csv
import os

import numpy as np
import pandas as pd
from colorthief import ColorThief

from igdb_api import download_image, query_igdb
from sklearn.cluster import KMeans

# Analysis settings
START_YEAR = 2013
END_YEAR = 2025
MAX_SCREENSHOTS_PER_GAME = 5  # possibly increase to 10

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "color_palettes.csv")


def main():
    # Prepare CSV
    if os.path.exists(OUTPUT_CSV):
        # Load existing rows to skip duplicates
        existing = pd.read_csv(OUTPUT_CSV)
        seen = set(zip(existing["Year"], existing["Game"], existing["Screenshot"]))
    else:
        # File doesn't exist → create header
        with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Year", "Game", "Screenshot", "Palette"])
        seen = set()

    # Open CSV in append mode
    with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        for year in range(START_YEAR, END_YEAR + 1):
            print(f"[INFO] Fetching all games from {year}...")
            offset = 0
            while True:
                games = query_igdb(year, offset=offset)
                if not games:
                    break  # no more games

                for game in games:
                    name = game.get("name", "Unknown")
                    screenshots = game.get("screenshots", [])

                    for sc in screenshots[:MAX_SCREENSHOTS_PER_GAME]:
                        image_path = download_image(sc["url"])
                        if not image_path:
                            continue

                        # Skip if already recorded
                        if (year, name, image_path) in seen:
                            continue

                        # Get palette
                        palette = []
                        thief = ColorThief(image_path)
                        palette = thief.get_palette(10)

                        # Cluster palette using k-means
                        if palette:
                            colors = np.array(palette)
                            kmeans = KMeans(min(5, len(colors)), random_state=42)
                            kmeans.fit(colors)
                            palette = [tuple(map(int, c)) for c in kmeans.cluster_centers_]
                        # Write row
                        writer.writerow([year, name, image_path, palette])
                        seen.add((year, name, image_path))
                        print(f"[INFO] Saved {name} ({year}) with palette {palette}")

                offset += len(games)
            print(f"[INFO] Finished fetching all games for {year}")

    print("[INFO] Data collection complete!")


if __name__ == "__main__":
    main()
