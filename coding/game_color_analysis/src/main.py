"""Main script to fetch game data and analyze color palettes from screenshots."""

import csv
import os

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# import colorgram
import fast_colorthief  # doesnt work wit 3.14
# from colorthief import ColorThief

from igdb_api import download_image, query_igdb


# Analysis settings
START_YEAR = 2023  # 1950  # Tennis for two 1958 OXO? 1952?
END_YEAR = 2025
MAX_SCREENSHOTS_PER_GAME = 3  # possibly increase to 10

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "game_info.csv")


def main():
    # Prepare CSV
    if os.path.exists(OUTPUT_CSV):
        # Load existing rows to skip duplicates
        current_csv = pd.read_csv(OUTPUT_CSV)
        processed = set(zip(current_csv["Year"], current_csv["Game"], current_csv["Screenshot"]))
    else:
        # Create new CSV with header
        with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Year", "Decade", "Game", "Screenshot", "Genres", "Themes", "Palette"])
        processed = set()

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

                    for screen in screenshots[:MAX_SCREENSHOTS_PER_GAME]:
                        image_path = download_image(screen["url"])
                        # Skip if download failed
                        if not image_path:
                            continue

                        # Skip if already recorded
                        if (year, name, image_path) in processed:
                            continue

                        # Get palette
                        palette = []
                        # color_thief = ColorThief(image_path)
                        try:
                            palette = fast_colorthief.get_palette(
                                image_path, color_count=10, quality=5
                            )
                            # palette = color_thief.get_palette(color_count=10, quality=5)

                        # colorgram throws error on completely white images
                        except RuntimeError as e:
                            print(f"[ERROR] Failed to extract palette from {image_path}: {e}")

                        # Cluster palette using k-means
                        if palette:
                            colors = np.array(palette)
                            kmeans = KMeans(n_clusters=min(5, len(colors)), random_state=42).fit(
                                colors
                            )
                            palette = [tuple(map(int, c)) for c in kmeans.cluster_centers_]

                        # Write row
                        writer.writerow(
                            [
                                year,
                                year // 10 * 10,
                                name,
                                image_path,
                                game.get("genres", "Unknown"),
                                game.get("themes", "Unknown"),
                                palette,
                            ]
                        )
                        processed.add((year, name, image_path))
                        print(
                            f"[INFO] Saved {name} ({year})"  # , genres: {game.get('genres', 'Unknown')}, themes: {game.get('themes', 'Unknown')}"
                        )

                offset += len(games)
            print(f"[INFO] Finished fetching all games for {year}")

    print("[INFO] Data collection complete!")


if __name__ == "__main__":
    main()
