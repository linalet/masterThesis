import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


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


def get_ranked_colors(df_row_or_group, count=5, filter_similarity=True):
    """
    The Universal Ranking Logic for the Thesis.
    Prioritizes: (Weight * 10) * (Saturation + 5)
    """
    r_cols = [f"C{i}_R" for i in range(1, 9)]
    g_cols = [f"C{i}_G" for i in range(1, 9)]
    b_cols = [f"C{i}_B" for i in range(1, 9)]
    w_cols = [f"C{i}_W" for i in range(1, 9)]

    # Handle both single rows (itertuples) and dataframes (groups)
    if isinstance(df_row_or_group, pd.DataFrame):
        r = df_row_or_group[r_cols].values.flatten()
        g = df_row_or_group[g_cols].values.flatten()
        b = df_row_or_group[b_cols].values.flatten()
        w = df_row_or_group[w_cols].values.flatten()
    else:
        r = np.array([getattr(df_row_or_group, c) for c in r_cols])
        g = np.array([getattr(df_row_or_group, c) for c in g_cols])
        b = np.array([getattr(df_row_or_group, c) for c in b_cols])
        w = np.array([getattr(df_row_or_group, c) for c in w_cols])

    mask = ~np.isnan(r) & (w > 0)
    r, g, b, w = r[mask], g[mask], b[mask], w[mask]

    if len(r) == 0:
        return []

    # 1. Bucket and Group
    r_b, g_b, b_b = (r // 15 * 15), (g // 15 * 15), (b // 15 * 15)
    sat = np.max([r, g, b], axis=0) - np.min([r, g, b], axis=0)

    temp = pd.DataFrame({"R": r_b, "G": g_b, "B": b_b, "W": w, "S": sat})
    grouped = (
        temp.groupby(["R", "G", "B"]).agg(total_w=("W", "sum"), max_s=("S", "max")).reset_index()
    )

    # 2. The Thesis Score
    grouped["score"] = (grouped["total_w"] * 10) * (grouped["max_s"] + 5)

    all_sorted = grouped.sort_values("score", ascending=False)

    if not filter_similarity:
        return all_sorted.head(count)

    # 4. Diversity Filter (The "Human Distinction" Fix)
    final_selection = []
    for row in all_sorted.itertuples():
        if len(final_selection) >= count:
            break
        is_similar = False
        for chosen in final_selection:
            dist = (
                (row.R - chosen.R) ** 2 + (row.G - chosen.G) ** 2 + (row.B - chosen.B) ** 2
            ) ** 0.5
            if dist < 50:
                is_similar = True
                break
        if not is_similar:
            final_selection.append(row)

    return final_selection


def get_representative_palette(yr_data, count=10):
    """Now uses the weighted logic for the Era Vibe!"""
    top_colors = get_ranked_colors(yr_data, count=count)
    return [f"#{int(c.R):02x}{int(c.G):02x}{int(c.B):02x}" for c in top_colors]


def on_selectbox_change():
    if st.session_state.all_time_box != "Select...":
        st.session_state.all_search = ""


def on_text_change():
    if st.session_state.all_search.strip() != "":
        st.session_state.all_time_box = "Select..."


def on_selectbox_change_dec():
    if st.session_state.dec_box != "Select...":
        st.session_state.dec_search = ""


def on_text_change_dec():
    if st.session_state.dec_search.strip() != "":
        st.session_state.dec_box = "Select..."
