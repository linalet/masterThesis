import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


def get_representative_palette(yr_data, count=10):
    if yr_data.empty:
        return []

    all_colors = []
    # We pool the top 3 clusters from every game to get the 'feel' of the era
    for i in range(1, 4):
        temp = yr_data[[f"C{i}_R", f"C{i}_G", f"C{i}_B"]].copy()
        temp.columns = ["R", "G", "B"]
        all_colors.append(temp)

    pool = pd.concat(all_colors).dropna()
    pool["sat"] = pool[["R", "G", "B"]].max(axis=1) - pool[["R", "G", "B"]].min(axis=1)

    # Bucket colors (Grouping similar shades)
    pool["R_B"] = (pool["R"] // 20 * 20).clip(0, 255)
    pool["G_B"] = (pool["G"] // 20 * 20).clip(0, 255)
    pool["B_B"] = (pool["B"] // 20 * 20).clip(0, 255)

    grouped = (
        pool.groupby(["R_B", "G_B", "B_B"])
        .agg(occurrence=("sat", "count"), avg_sat=("sat", "mean"))
        .reset_index()
    )

    # LOGIC FIX: If the average saturation is extremely low (< 10), rank by count alone.
    # This prevents black/white/grey colors from being ignored.
    if grouped["avg_sat"].mean() < 10:
        grouped["rank_score"] = grouped["occurrence"]
    else:
        # For colored games, prioritize vibrant hues while still considering frequency
        grouped["rank_score"] = grouped["occurrence"] * (grouped["avg_sat"] + 15)
    top = grouped.nlargest(count, "rank_score")
    return [f"#{int(r):02x}{int(g):02x}{int(b):02x}" for r, g, b in zip(top.R_B, top.G_B, top.B_B)]


@st.cache_data
def load_data(path):
    # Load the pre-processed file
    df = pd.read_parquet(path)
    rename_map = {col.lower(): col for col in df.columns}

    if "game" in rename_map:
        df = df.rename(columns={rename_map["game"]: "Game"})

    if "Game" not in df.columns:
        # Check if maybe 'Name' was used instead?
        if "name" in rename_map:
            df = df.rename(columns={rename_map["name"]: "Game"})
        else:
            available = ", ".join(df.columns)
            raise KeyError(f"Critical Column 'Game' missing from Parquet. Available: {available}")

    standard_cols = ["Year", "Developers", "Themes", "Genres", "Art_Style", "Screenshot"]
    for col in standard_cols:
        lower_col = col.lower()
        if lower_col in rename_map and col not in df.columns:
            df = df.rename(columns={rename_map[lower_col]: col})

    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")

    df["Dev_Set"] = df["Developers"].apply(lambda x: set(x.split("|")))
    df["Theme_Set"] = df["Themes"].apply(lambda x: set(x.split("|")))
    df["Genre_Set"] = df["Genres"].apply(lambda x: set(x.split("|")))

    # 2. Get Global Lists for UI Selectboxes
    all_devs = df["Developers"].str.split("|").explode().str.strip()
    unique_devs = sorted(all_devs[all_devs != ""].unique().tolist())
    top_studios = all_devs[all_devs != ""].value_counts().nlargest(50).index.tolist()
    # 3. Filter for Thesis Scope
    df_indexed = df.set_index("Game", drop=False)

    return df_indexed, unique_devs, top_studios


def render_color_strip(data_subset, label, sub_label=""):
    pal = get_representative_palette(data_subset, count=10)
    c1, c2, c3 = st.columns([1, 2, 6])
    c1.write(f"**{label}**")
    c2.caption(sub_label)
    with c3:
        # Horizontal Pillar View for consistent thesis formatting
        html = '<div style="display: flex; height: 25px; border-radius: 4px; overflow: hidden; margin-bottom: 8px; border: 1px solid #444;">'
        for color in pal:
            html += f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
