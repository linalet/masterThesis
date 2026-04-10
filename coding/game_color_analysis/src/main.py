"""Main script to fetch game data and analyze color palettes from screenshots."""

import csv
import os
import pandas as pd
from PIL import Image

from igdb_api import download_image, query_igdb


START_YEAR = 1990
END_YEAR = 2026
SCREENSHOT_COUNT = 5  # possibly increase to 10
COLOR_COUNT = 10

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "octree_game_data.csv")

# List of keywords to filter nsfw images
NSFW_WORDS = [
    "erotica",
    "hentai",
    "nsfw",
    "nudity",
    "sexual content",
    "adult",
    "pornographic",
    "porn",
    "porno",
    "sex",
    "sexy",
    "eroge",
]


def get_palette(image_path, n_clusters=10):
    """
    Gets the color palette using Median Cut.
    Returns a list of tuples sorted by weight.
    """
    try:
        with Image.open(image_path) as image:
            image = image.convert("RGB")
            quantized_image = image.quantize(colors=n_clusters, method=Image.Quantize.MEDIANCUT)
            quantized_image = image.quantize(colors=20, method=Image.Quantize.FASTOCTREE)

            # get palettes
            raw_palette = quantized_image.getpalette()[: n_clusters * 3]
            colors = [tuple(raw_palette[i : i + 3]) for i in range(0, len(raw_palette), 3)]

            color_counts = quantized_image.getcolors()
            pixel_count = sum(count for count, index in color_counts)

            # calculate weights
            palette = []
            for count, index in color_counts:
                if index < len(colors):
                    r, g, b = colors[index]
                    weight = count / pixel_count
                    palette.append((r, g, b, weight))

        palette.sort(key=lambda x: x[3], reverse=True)
        return palette
    except Exception as e:
        print(f"[ERROR] Could not process {image_path}: {e}")
        return []


def main():
    # Prepare CSV
    color_headers = []
    for i in range(1, COLOR_COUNT + 1):
        color_headers.extend([f"C{i}_R", f"C{i}_G", f"C{i}_B", f"C{i}_W"])
    header = [
        "Year",
        "Decade",
        "Game",
        "Screenshot",
        "Genres",
        "Themes",
        "Keywords",
        "Player_Perspective",
        "Developers",
        "Is_NSFW",
    ] + color_headers

    if os.path.exists(OUTPUT_CSV):
        # Skip processed screenshots
        processed = set(
            pd.read_csv(OUTPUT_CSV, usecols=["Screenshot"])["Screenshot"].astype(str).tolist()
        )
        # current_csv = pd.read_csv(OUTPUT_CSV, low_memory=False)
        # processed = set(current_csv["Screenshot"].astype(str).tolist())
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(header)
        processed = set()

    with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        for year in range(START_YEAR, END_YEAR + 1):
            print(f"[INFO] Getting games from {year}...")
            offset = 0
            while True:
                games = query_igdb(year, offset=offset)
                if not games:
                    break  # no more games
                # get data
                for game in games:
                    name = game.get("name", "Unknown")
                    devs = "|".join(
                        [
                            c["company"]["name"]
                            for c in game.get("involved_companies", [])
                            if c.get("developer")
                        ]
                    )
                    genres = "|".join(g["name"] for g in game.get("genres", []) if "name" in g)
                    themes = "|".join(t["name"] for t in game.get("themes", []) if "name" in t)
                    keywords = "|".join(k["name"] for k in game.get("keywords", []) if "name" in k)
                    perspective = "|".join(
                        p["name"] for p in game.get("player_perspectives", []) if "name" in p
                    )
                    combined_text = f"{genres} {themes} {keywords} {name}".lower()
                    is_nsfw = 1 if any(word in combined_text for word in NSFW_WORDS) else 0
                    # screenshots = game.get("screenshots", [])

                    for screen in game.get("screenshots", [])[:SCREENSHOT_COUNT]:
                        image_path = download_image(screen["url"])
                        # Skip if download failed or already recorded
                        if not image_path or image_path in processed:
                            continue

                        palette = get_palette(image_path, n_clusters=COLOR_COUNT)
                        color_data = []
                        for i in range(COLOR_COUNT):
                            if i < len(palette):
                                color_data.extend(list(palette[i]))
                            else:
                                color_data.extend([None, None, None, 0.0])
                        writer.writerow(
                            [
                                year,
                                year // 10 * 10,
                                name,
                                image_path,
                                genres,
                                themes,
                                keywords,
                                perspective,
                                devs,
                                is_nsfw,
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
