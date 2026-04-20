"""Main script to fetch game data and analyze color palettes from screenshots."""

import csv
import os
import pandas as pd
from PIL import Image

from igdb_api import download_image, query_igdb


START_YEAR = 1950
END_YEAR = 2026
SCREENSHOT_COUNT = 5  # possibly increase to 10
COLOR_COUNT = 10

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
# OUTPUT_CSV = os.path.join(DATA_DIR, "game_data.csv")
OUTPUT_PARQUET = os.path.join(DATA_DIR, "game_data.parquet")

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
    Gets the color palette using Octree quantization.
    Returns a list of tuples sorted by weight.
    """
    try:
        with Image.open(image_path) as image:
            image = image.convert("RGB")
            # quantized_image = image.quantize(colors=n_clusters, method=Image.Quantize.MEDIANCUT)
            quantized_image = image.quantize(colors=n_clusters, method=Image.Quantize.FASTOCTREE)

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

    if os.path.exists(OUTPUT_PARQUET):
        # Skip processed screenshots
        processed = set(
            pd.read_parquet(OUTPUT_PARQUET, columns=["Screenshot"])["Screenshot"].tolist()
        )
        append_mode = True
    else:
        processed = set()
        append_mode = False
    buffer = []
    counter = 0
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"[INFO] Getting games from {year}...")
        decade = (year // 10) * 10
        offset = 0
        while True:
            games = query_igdb(year, offset=offset)
            if not games:
                break  # no more games
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
                    url = screen["url"]
                    if url in processed:
                        continue
                    image_path = download_image(url)
                    # Skip if download failed or already recorded
                    if not image_path:
                        continue

                    palette = get_palette(image_path, n_clusters=COLOR_COUNT)
                    row = {
                        "Year": year,
                        "Decade": decade,
                        "Game": game.get("name", "Unknown"),
                        "Screenshot": url,
                        "Developers": devs,
                        "Genres": genres,
                        "Themes": themes,
                        "Keywords": keywords,
                        "Player_Perspective": perspective,
                        "Is_NSFW": is_nsfw,
                    }
                    for i in range(COLOR_COUNT):
                        r, g, b, w = palette[i] if i < len(palette) else (None, None, None, 0.0)
                        row.update(
                            {f"C{i + 1}_R": r, f"C{i + 1}_G": g, f"C{i + 1}_B": b, f"C{i + 1}_W": w}
                        )

                    buffer.append(row)
                    processed.add(image_path)
                counter += 1

                if counter % 500 == 0:
                    df_flush = pd.DataFrame(buffer)
                    df_flush.to_parquet(
                        OUTPUT_PARQUET, engine="fastparquet", append=append_mode, index=False
                    )
                    append_mode = True
                    buffer = []
                    print(f"💾 Milestone: {counter} games saved to disk. RAM cleared.")

                print(f"[INFO] Saved {name} ({year})")

            offset += len(games)
        print(f"[INFO] Finished all games for {year}")
    if buffer:
        pd.DataFrame(buffer).to_parquet(
            OUTPUT_PARQUET, engine="fastparquet", append=append_mode, index=False
        )
        print("🏁 Final batch saved. Collection complete!")
    df_final = pd.read_parquet(OUTPUT_PARQUET)
    df_final.to_csv(os.path.join(DATA_DIR, "human_readable_backup.csv"), index=False)
    print("[INFO] Data collection complete!")


if __name__ == "__main__":
    main()
