import pandas as pd
import ast
import matplotlib.pyplot as plt
from collections import Counter

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("color_palettes.csv")

# Convert palette string back into Python list
df["Palette"] = df["Palette"].apply(lambda x: ast.literal_eval(x))

# Add a decade column
df["Decade"] = (df["Year"] // 10) * 10

# Flatten colors by decade
decade_colors = {}
for _, row in df.iterrows():
    decade = row["Decade"]
    colors = row["Palette"]
    if decade not in decade_colors:
        decade_colors[decade] = []
    decade_colors[decade].extend(colors)

# =========================
# VISUALIZE COLOR TRENDS
# =========================
def plot_decade_palette(decade, colors, top_n=10):
    """Plot most common colors for a given decade."""
    counter = Counter(colors)
    most_common = counter.most_common(top_n)

    plt.figure(figsize=(10, 2))
    for i, (color, count) in enumerate(most_common):
        plt.fill_between([i, i+1], 0, 1, color=[c/255 for c in color])
        plt.text(i+0.5, -0.1, str(color), ha="center", va="top", fontsize=8, rotation=90)
    plt.axis("off")
    plt.title(f"Top {top_n} Colors in {decade}s")
    plt.show()

# Example: plot a single decade
plot_decade_palette(2000, decade_colors[2000])

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

# Example: full timeline
plot_decade_timeline(decade_colors, top_n=8)
