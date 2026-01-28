"""Streamlit app to explore game color palettes from screenshots."""

import ast
import math
import os
from collections import Counter

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans

# -----------------------------
# Config
# -----------------------------
DATA_CSV = r"C:\Users\nina\Documents\UNI\SEM\thesis\coding\game_color_analysis\data\processed_color_data.csv"
PAGE_SIZE = 12
TOP_COLORS = 10
CLUSTER_COLORS = 8


# -----------------------------
# Helper functions
# -----------------------------
def is_dark_color(color, threshold=40):
    r, g, b = color
    brightness = math.sqrt(0.299 * (r**2) + 0.587 * (g**2) + 0.114 * (b**2))
    return brightness < threshold


def remove_dark_colors(palette, threshold=40):
    return [c for c in palette if not is_dark_color(c, threshold)]


def color_distance(c1, c2):
    return np.linalg.norm(np.array(c1) - np.array(c2))


def find_similar_games(df, target_color, threshold=40):
    matches = []
    for _, row in df.iterrows():
        for color in row["Palette"]:
            if color_distance(color, target_color) <= threshold:
                matches.append(row)
                break
    return pd.DataFrame(matches)


def draw_palette(palette, height=25):
    """Render a palette as horizontal color blocks."""
    if not palette:
        st.write("_No palette_")
        return

    cols = st.columns(len(palette))
    for col, color in zip(cols, palette):
        hex_color = "#%02x%02x%02x" % tuple(color)
        col.markdown(
            f"<div style='background-color:{hex_color}; height:{height}px;'></div>",
            unsafe_allow_html=True,
        )


# -----------------------------
# Load data (cached)
# -----------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["Palette"] = df["Palette"].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])
    return df


df = load_data(DATA_CSV)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Filters")

years = sorted(df["Year"].unique())
decades = sorted(df["Decade"].unique())

selected_year = st.sidebar.selectbox("Select Year", [None] + years)
selected_decade = st.sidebar.selectbox("Select Decade", [None] + decades)

remove_dark = st.sidebar.checkbox("Remove dark shades", value=True)
dark_threshold = st.sidebar.slider("Darkness threshold", 10, 120, 40)

cluster_colors = st.sidebar.checkbox("Cluster colors (k-means)", value=True)

st.sidebar.header("Cluster Exploration")
explore_cluster = st.sidebar.checkbox("Enable cluster exploration", value=False)
cluster_threshold = st.sidebar.slider("Color similarity threshold", 5, 100, 40)

# -----------------------------
# Filter dataset
# -----------------------------
filtered = df
if selected_year is not None:
    filtered = filtered[filtered["Year"] == selected_year]
if selected_decade is not None:
    filtered = filtered[filtered["Decade"] == selected_decade]

if remove_dark:
    filtered = filtered.copy()
    filtered["Palette"] = filtered["Palette"].apply(lambda p: remove_dark_colors(p, dark_threshold))

st.title("Game Color Palette Explorer")
st.caption(f"Showing {len(filtered)} screenshots")


# -----------------------------
# Top colors
# -----------------------------
@st.cache_data
def get_top_colors(df, use_clustering=True):
    all_colors = []
    for p in df["Palette"]:
        all_colors.extend(p)
    if not all_colors:
        return []

    colors = np.array(all_colors)
    if use_clustering and len(colors) >= CLUSTER_COLORS:
        km = KMeans(n_clusters=CLUSTER_COLORS, random_state=42)
        km.fit(colors)
        return [tuple(c) for c in np.rint(km.cluster_centers_).astype(int)]
    else:
        return [c for c, _ in Counter(all_colors).most_common(TOP_COLORS)]


top_colors = get_top_colors(filtered, cluster_colors)

st.subheader("Top Colors")
draw_palette(top_colors, height=50)

# -----------------------------
# Screenshots (paginated)
# -----------------------------
st.subheader("Screenshots & Palettes")

total = len(filtered)
max_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
page = st.number_input("Page", 1, max_page, 1)

batch = filtered.iloc[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

cols = st.columns(3)
i = 0
for _, row in batch.iterrows():
    with cols[i % 3]:
        st.write(f"**{row['Game']} ({row['Year']})**")
        if os.path.exists(row["Screenshot"]):
            st.image(row["Screenshot"], width=250)
        else:
            st.write("_Missing screenshot_")
        draw_palette(row["Palette"])
    i += 1

# -----------------------------
# Timeline
# -----------------------------
st.subheader("Timeline (Top Colors by Year)")


@st.cache_data
def compute_timeline(df):
    rows = []
    for y in sorted(df["Year"].unique()):
        colors = []
        for p in df[df["Year"] == y]["Palette"]:
            colors.extend(p)
        if not colors:
            continue

        colors = np.array(colors)
        if cluster_colors and len(colors) >= CLUSTER_COLORS:
            km = KMeans(n_clusters=CLUSTER_COLORS, random_state=42)
            km.fit(colors)
            year_colors = [tuple(c) for c in np.rint(km.cluster_centers_).astype(int)]
        else:
            year_colors = [c for c, _ in Counter(colors.tolist()).most_common(5)]

        for i, c in enumerate(year_colors):
            rows.append({"Year": y, "Position": i, "Color": "#%02x%02x%02x" % tuple(c)})
    return pd.DataFrame(rows)


timeline_df = compute_timeline(filtered)

if not timeline_df.empty:
    fig = px.scatter(
        timeline_df,
        x="Position",
        y="Year",
        color="Color",
        color_discrete_sequence=timeline_df["Color"].tolist(),
        size=[20] * len(timeline_df),
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Cluster exploration
# -----------------------------
if explore_cluster and top_colors:
    cluster_color = st.selectbox(
        "Select cluster color",
        top_colors,
        format_func=lambda c: "#%02x%02x%02x" % tuple(c),
    )

    similar = find_similar_games(filtered, cluster_color, cluster_threshold)

    st.subheader(f"Games containing {'#%02x%02x%02x' % cluster_color}")

    if similar.empty:
        st.write("_No matching games_")
    else:
        max_page_sim = max(1, (len(similar) + PAGE_SIZE - 1) // PAGE_SIZE)
        page_sim = st.number_input("Cluster page", 1, max_page_sim, 1, key="cluster")

        batch_sim = similar.iloc[(page_sim - 1) * PAGE_SIZE : page_sim * PAGE_SIZE]

        cols_sim = st.columns(3)
        i = 0
        for _, row in batch_sim.iterrows():
            with cols_sim[i % 3]:
                st.write(f"**{row['Game']} ({row['Year']})**")
                if os.path.exists(row["Screenshot"]):
                    st.image(row["Screenshot"], width=250)
                draw_palette(row["Palette"])
            i += 1
