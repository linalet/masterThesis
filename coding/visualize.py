import pandas as pd
import ast
import matplotlib.pyplot as plt
from collections import Counter

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("game_color_palettes.csv")

# Convert palette string back into Python list
df["Palette"] = df["Palette"].apply(lambda x: ast.literal_eval(x))

# Flatten colors by year
year_colors = {}
for _, row in df.iterrows():
    year = row["Year"]
    colors = row["Palette"]
    if year not in year_colors:
        year_colors[year] = []
    year_colors[year].extend(colors)

# =========================
# VISUALIZE COLOR TRENDS
# =========================
def plot_year_palette(year, colors, top_n=8):
    """Plot most common colors for a given year."""
    counter = Counter(colors)
    most_common = counter.most_common(top_n)

    plt.figure(figsize=(8, 2))
    for i, (color, count) in enumerate(most_common):
        plt.fill_between([i, i+1], 0, 1, color=[c/255 for c in color])
        plt.text(i+0.5, -0.1, str(color), ha="center", va="top", fontsize=8, rotation=90)
    plt.axis("off")
    plt.title(f"Top {top_n} Colors in {year}")
    plt.show()

# Example: plot palettes for a single year
plot_year_palette(2003, year_colors[2003])

# =========================
# TREND OVER TIME
# =========================
def plot_color_timeline(year_colors, top_n=5):
    """Show top colors across years as a timeline."""
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

# Example: full timeline
plot_color_timeline(year_colors, top_n=5)
