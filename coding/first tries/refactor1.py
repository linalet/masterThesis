import os
import requests
import csv
from colorthief import ColorThief
import pandas as pd
import ast
import matplotlib.pyplot as plt
from collections import Counter

# =============================
# CONFIG
# =============================

CLIENT_ID = "6k1gmqbtqyihlzrqijshniy5fs3xis"
ACCESS_TOKEN = "tf6tmtwd8q8s6vuhrxyjir9wjxmv6k"
# CLIENT_SECRET= "gg7mz9dsnkpfnt3d7f6l5xkvhsmu6u"

START_YEAR = 2020
END_YEAR = 2025
OUTPUT_FOLDER = "screenshots"
OUTPUT_CSV = "color_palettes.csv"

# =============================
# IGDB API SETUP
# =============================

HEADERS = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def query_igdb(year, limit=20):
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

def extract_palette(image_path, color_count=10):
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
# path = 'C:/Users/nina/Documents/UNI/SEM/thesis/coding/data/color_palettes.csv'
# if not os.path.exists(path):
with open(OUTPUT_CSV, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Year", "Game", "Screenshot", "Palette"])  # header row

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Fetching games from {year}...")
        try:
            games = query_igdb(year, limit=5) #max 44
        except Exception as e:
            print(f"Failed to fetch {year}: {e}")
            continue

        for game in games:
            name = game.get("name", "Unknown")
            screenshots = game.get("screenshots", [])

            for sc in screenshots[:5]:  # only take 2 screenshots per game
                try:
                    img_path = download_image(sc["url"])
                    palette = extract_palette(img_path)
                    writer.writerow([year, name, img_path, palette])
                    print(f"Saved {name} ({year}) with palette {palette}")
                except Exception as e:
                    print(f"Error processing screenshot: {e}")
        print(f"Games from {year} ready")

df = pd.read_csv("color_palettes.csv")
# Convert palette string back into Python list
df["Palette"] = df["Palette"].apply(lambda x: ast.literal_eval(x))

# Add a decade column
df["Decade"] = (df["Year"] // 10) * 10

# Flatten colors by year and decade
year_colors = {}
decade_colors = {}
for _, row in df.iterrows():
    year = row["Year"]
    decade = row["Decade"]
    colors = row["Palette"]
    if year not in year_colors:
        year_colors[year] = []
    year_colors[year].extend(colors)
    if decade not in decade_colors:
        decade_colors[decade] = []
    decade_colors[decade].extend(colors)

# =========================
# VISUALIZE COLOR TRENDS
# =========================

def plot_year_palette(year, colors, top_n=8):
    """Plot top_n most common colors for a given year."""
    counter = Counter(colors)
    most_common = counter.most_common(top_n)

    plt.figure(figsize=(top_n, 2))
    for i, (color, count) in enumerate(most_common):
        plt.fill_between([i, i+1], 0, 1, color=[c/255 for c in color])
        plt.text(i+0.5, -0.1, str(color), ha="center", va="top", fontsize=8, rotation=90)
    plt.axis("off")
    plt.title(f"Top {top_n} Colors in {year}")
    plt.show()

def plot_decade_palette(decade, colors, top_n=10):
    """Plot top_n most common colors for a given decade."""
    counter = Counter(colors)
    most_common = counter.most_common(top_n)

    plt.figure(figsize=(top_n, 2))
    for i, (color, count) in enumerate(most_common):
        plt.fill_between([i, i+1], 0, 1, color=[c/255 for c in color])
        plt.text(i+0.5, -0.1, str(color), ha="center", va="top", fontsize=8, rotation=90)
    plt.axis("off")
    plt.title(f"Top {top_n} Colors in {decade}s")
    plt.show()

# =========================
# TREND OVER TIME
# =========================

def plot_color_timeline(year_colors, top_n=5):
    """Show top_n most common colors across years as a timeline."""
    years = sorted(year_colors.keys())
    top_colors_by_year = {}

    for year in years:
        counter = Counter(year_colors[year])
        top_colors_by_year[year] = [c for c, _ in counter.most_common(top_n)]

    fig, ax = plt.subplots(figsize=(12, len(years) * 0.4))
    for i, year in enumerate(years):
        for j, color in enumerate(top_colors_by_year[year]):
            ax.add_patch(plt.Rectangle((j, i), 1, 1, color=[c/255 for c in color]))
        ax.text(-0.5, i+0.5, str(year), va="center", fontsize=9)

    ax.set_xlim(0, top_n)
    ax.set_ylim(0, len(years))
    ax.axis("off")
    plt.title(f"Top {top_n} Dominant Colors by Year")
    plt.show()

# =========================
# DECADE TIMELINE
# =========================
def plot_decade_timeline(decade_colors, top_n=8):
    """Show top colors across decades as a timeline."""
    decades = sorted(decade_colors.keys())
    top_colors_by_decade = {}

    for decade in decades:
        counter = Counter(decade_colors[decade])
        top_colors_by_decade[decade] = [c for c, _ in counter.most_common(top_n)]

    fig, ax = plt.subplots(figsize=(12, len(decades) * 0.6))
    for i, decade in enumerate(decades):
        for j, color in enumerate(top_colors_by_decade[decade]):
            ax.add_patch(plt.Rectangle((j, i), 1, 1, color=[c/255 for c in color]))
        ax.text(-0.5, i+0.5, f"{decade}s", va="center", fontsize=10)

    ax.set_xlim(0, top_n)
    ax.set_ylim(0, len(decades))
    ax.axis("off")
    plt.title(f"Top {top_n} Dominant Colors by Decade")
    plt.show()

# Example
# plot_year_palette(2000, year_colors[2000])
# plot_decade_palette(1980, decade_colors[1980])
plot_decade_timeline(decade_colors, top_n=10)
plot_color_timeline(year_colors, top_n=10)
