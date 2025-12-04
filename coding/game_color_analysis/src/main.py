import csv
from config import START_YEAR, END_YEAR, MAX_SCREENSHOTS_PER_GAME, COLOR_COUNT, OUTPUT_CSV
from igdb_api import query_igdb, download_image
from color_extraction import extract_palette, cluster_palette

def main():
    # Create CSV and write headers
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Year", "Game", "Screenshot", "Palette"])

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
                        img_path = download_image(sc["url"])
                        if not img_path:
                            continue

                        palette = extract_palette(img_path, COLOR_COUNT)
                        clustered_palette = cluster_palette(palette, n_clusters=5)

                        writer.writerow([year, name, img_path, clustered_palette])
                        print(f"[INFO] Saved {name} ({year}) with palette {clustered_palette}")

                offset += len(games)
            print(f"[INFO] Finished fetching all games for {year}")

    print("[INFO] Data collection complete!")

if __name__ == "__main__":
    main()
