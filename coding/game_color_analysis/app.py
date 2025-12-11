import streamlit as st
import pandas as pd
import ast
import os
import math
from collections import Counter
from sklearn.cluster import KMeans
import numpy as np
import plotly.express as px

# -----------------------------
# Config
# -----------------------------
DATA_CSV = r"C:\Users\nina\Documents\UNI\SEM\thesis\coding\game_color_analysis\src\processed_color_data.csv"
PAGE_SIZE = 12   # screenshots per page
TOP_COLORS = 10  # colors to show in top palette
CLUSTER_COLORS = 8  # number of clusters for k-means

# -----------------------------
# Cached data loading
# -----------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["Palette"] = df["Palette"].apply(
        lambda x: ast.literal_eval(x) if pd.notnull(x) else []
    )
    return df

df = load_data(DATA_CSV)

# -----------------------------
# Perceptual brightness filter
# -----------------------------
def is_dark_color(color, threshold=40):
    """HSP brightness model; returns True if perceived as dark."""
    r, g, b = color
    brightness = math.sqrt(0.299*(r**2) + 0.587*(g**2) + 0.114*(b**2))
    return brightness < threshold

def remove_dark_colors(palette, threshold=40):
    return [c for c in palette if not is_dark_color(c, threshold)]

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")
years = sorted(df["Year"].unique())
decades = sorted(df["Decade"].unique())

selected_year = st.sidebar.selectbox("Select Year", [None] + years)
selected_decade = st.sidebar.selectbox("Select Decade", [None] + decades)
remove_dark = st.sidebar.checkbox("Remove dark shades", value=True)
dark_threshold = st.sidebar.slider("Darkness threshold", 10, 120, 40)
cluster_colors = st.sidebar.checkbox("Cluster colors (k-means)", value=True)

# -----------------------------
# Filter dataset
# -----------------------------
filtered = df
if selected_year is not None:
    filtered = filtered[filtered["Year"] == selected_year]
if selected_decade is not None:
    filtered = filtered[filtered["Decade"] == selected_decade]

# Apply dark color filter
if remove_dark:
    filtered["Palette"] = filtered["Palette"].apply(lambda p: remove_dark_colors(p, dark_threshold))

st.title("Game Color Palette Explorer (Clustered + Filtered)")
st.caption(f"Showing {len(filtered)} matching screenshots")

# -----------------------------
# Compute top colors with optional clustering
# -----------------------------
@st.cache_data
def get_top_colors(df, n_colors=TOP_COLORS, use_clustering=True, n_clusters=CLUSTER_COLORS):
    all_colors = []
    for p in df["Palette"]:
        all_colors.extend(p)
    if not all_colors:
        return []

    all_colors_arr = np.array(all_colors)

    if use_clustering and len(all_colors_arr) >= n_clusters:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(all_colors_arr)
        cluster_centers = np.rint(kmeans.cluster_centers_).astype(int)
        return [tuple(c) for c in cluster_centers]
    else:
        # fallback: most common colors
        return [c for c,_ in Counter(all_colors).most_common(n_colors)]

top_colors = get_top_colors(filtered, use_clustering=cluster_colors)

# -----------------------------
# Display top colors
# -----------------------------
st.subheader("Top Colors")
cols = st.columns(len(top_colors))
for col, color in zip(cols, top_colors):
    hex_color = '#%02x%02x%02x' % tuple(color)
    col.markdown(f"<div style='background-color:{hex_color}; height:50px;'></div>", unsafe_allow_html=True)
    col.write(hex_color)

# -----------------------------
# Paginated screenshot viewer
# -----------------------------
st.subheader("Screenshots & Palettes")
total = len(filtered)
max_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
page = st.number_input("Page", min_value=1, max_value=max_page, step=1)
start = (page - 1) * PAGE_SIZE
end = start + PAGE_SIZE
batch = filtered.iloc[start:end]

cols = st.columns(3)
i = 0
for _, row in batch.iterrows():
    with cols[i % 3]:
        st.write(f"**{row['Game']} ({row['Year']})**")
        img_path = row["Screenshot"]
        if os.path.exists(img_path):
            st.image(img_path, width=250)
        else:
            st.write("_Missing screenshot_")
        st.write("Palette:", row["Palette"])
    i += 1

# -----------------------------
# Timeline visualization (Plotly)
# -----------------------------
st.subheader("Timeline (Top Colors by Year)")

@st.cache_data
def compute_timeline(df, n_top=5, use_clustering=True, n_clusters=CLUSTER_COLORS):
    timeline_data = []
    for y in sorted(df["Year"].unique()):
        year_df = df[df["Year"] == y]
        # Gather all colors
        all_colors = []
        for p in year_df["Palette"]:
            all_colors.extend(p)
        if not all_colors:
            continue
        colors_arr = np.array(all_colors)

        # cluster or take top N
        if use_clustering and len(colors_arr) >= n_clusters:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            kmeans.fit(colors_arr)
            cluster_centers = np.rint(kmeans.cluster_centers_).astype(int)
            top_colors_year = [tuple(c) for c in cluster_centers]
        else:
            top_colors_year = [c for c,_ in Counter(all_colors).most_common(n_top)]

        for pos, color in enumerate(top_colors_year):
            timeline_data.append({
                "Year": y,
                "Position": pos,
                "ColorHex": '#%02x%02x%02x' % tuple(color)
            })
    return pd.DataFrame(timeline_data)

timeline_df = compute_timeline(filtered, use_clustering=cluster_colors)

if not timeline_df.empty:
    fig = px.scatter(
        timeline_df,
        x="Position",
        y="Year",
        color="ColorHex",
        color_discrete_sequence=timeline_df["ColorHex"].tolist(),
        size=[20]*len(timeline_df)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("_No data to show timeline._")
