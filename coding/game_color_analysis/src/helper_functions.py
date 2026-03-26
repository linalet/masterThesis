import streamlit as st
import pandas as pd
import plotly.express as px


studio_map = {
    "nintendo": [
        "nintendo r&d",
        "nintendo ead",
        "nintendo entertainment",
        "nintendo ird",
        "nintendo tokyo",
    ],
    "ubisoft": [
        "ubi soft",
        "ubisoft montreal",
        "ubisoft toronto",
        "ubisoft paris",
        "ubisoft entertainment",
    ],
    "sega": ["sega am", "sega wow", "sega technical institute", "sonic team"],
    "capcom": ["capcom production", "capcom development"],
    "konami": ["konami computer entertainment", "konami tokyo", "konami osaka"],
}


def normalize_studio_name(dev_string):
    # Split pipe-connected studios first
    parts = [p.strip() for p in dev_string.split("|")]
    cleaned_parts = []

    for part in parts:
        found_parent = False
        for parent, aliases in studio_map.items():
            if part == parent or any(alias in part for alias in aliases):
                cleaned_parts.append(parent)
                found_parent = True
                break
        if not found_parent:
            cleaned_parts.append(part)

    # Return joined string to keep original data structure for pooling
    return "|".join(list(set(cleaned_parts)))


def classify_taxonomy(row):
    text = f"{row['Keywords']} {row['Themes']} {row['Genres']}".lower()
    perspective = str(row.get("Player_Perspective", "")).lower().strip()

    # III. ABSTRACTION
    if any(w in text for w in ["text-based", "experimental", "psychedelic", "ascii"]):
        return "Abstraction: Symbolic"
    if any(w in text for w in ["flat art", "silhouette", "geometric", "minimalist"]):
        return "Abstraction: Minimalist"

    # I. REALISM
    if any(w in text for w in ["photoreal", "ray-tracing", "pbr", "realistic", "4k"]):
        return "Realism: Photoreal"
    if any(w in text for w in ["cinematic", "fantasy realism", "atmospheric"]):
        return "Realism: Stylized"  # literally 0 games

    # II. STYLIZATION
    if any(
        w in text
        for w in ["watercolor", "hand-painted", "comic", "cel-shade", "hand-drawn", "sketch"]
    ):
        return "Stylization: Illustrative"
    if any(w in text for w in ["anime", "manga", "chibi", "cartoon"]):
        return "Stylization: Caricature"
    if any(w in text for w in ["pixel", "8-bit", "16-bit", "voxel"]):
        return "Stylization: Pixel Art"
    if any(
        w in text
        for w in ["claymation", "papercraft", "puppet", "stop-motion", "felt", "ballpoint"]
    ):
        return "Stylization: Material-Based"

    # fallback
    if row["Year"] < 1970:
        if "text" in perspective:
            return "Abstraction: Symbolic"
        return "Abstraction: Minimalist"
    if any(w in text for w in ["3d", "3-D"]):
        return "Unclassified 3D"
    if any(w in text for w in ["2d", "2-D"]):
        return "Unclassified 2D"
    return "Unclassified"


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

    # 1. Quick Re-calc of runtime-only objects (Sets aren't saved in Parquet)
    df["Dev_Set"] = df["Developers"].apply(lambda x: set(x.split("|")))
    df["Theme_Set"] = df["Themes"].apply(lambda x: set(x.split("|")))
    df["Genre_Set"] = df["Genres"].apply(lambda x: set(x.split("|")))

    # 2. Get Global Lists for UI Selectboxes
    all_devs_series = df["Developers"].str.split("|").explode().str.strip()
    top_studios_global = (
        all_devs_series[all_devs_series != ""].value_counts().nlargest(50).index.tolist()
    )
    unique_devs = sorted(all_devs_series[all_devs_series != ""].unique().tolist())

    # 3. Filter for Thesis Scope
    df_filtered = df[df["Year"] > 1950].copy()

    return df_filtered, unique_devs, top_studios_global


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


#
#
#
def render_saturation_heatmap(plot_df):
    """
    Visualizes the 'Vibrancy Dip' of the 2000s vs other eras.
    """
    st.subheader("📊 Colorfulness Heatmap (The 'Vibrancy Dip')")
    st.write("Tracks the average saturation levels across academic taxonomies over time.")

    # Group by Year and Level 1 (Intent)
    plot_df["Level1"] = plot_df["Art_Style"].apply(lambda x: x.split(":")[0])
    heatmap_data = plot_df.groupby(["Year", "Level1"])["saturation"].mean().reset_index()

    fig = px.density_heatmap(
        heatmap_data,
        x="Year",
        y="Level1",
        z="saturation",
        color_continuous_scale="Viridis",
        labels={"saturation": "Avg Saturation"},
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def get_weighted_representative_palette(yr_data, count=8):
    all_colors = []

    # 1. Flatten the data: Turn every C1-C8 from every row into individual data points
    for i in range(1, 9):
        temp = yr_data[[f"C{i}_R", f"C{i}_G", f"C{i}_B", f"C{i}_W"]].copy()
        temp.columns = ["R", "G", "B", "W"]
        # Calculate saturation for ranking
        temp["sat"] = temp[["R", "G", "B"]].max(axis=1) - temp[["R", "G", "B"]].min(axis=1)
        all_colors.append(temp)

    # Combine everything into one big pool of colors found in this game
    pool = pd.concat(all_colors).dropna()

    # 2. Bucket the colors to group similar ones
    pool["R_B"] = (pool["R"] // 20 * 20).clip(0, 255)
    pool["G_B"] = (pool["G"] // 20 * 20).clip(0, 255)
    pool["B_B"] = (pool["B"] // 20 * 20).clip(0, 255)

    # 3. Group by bucket
    grouped = (
        pool.groupby(["R_B", "G_B", "B_B"])
        .agg(total_weight=("W", "sum"), max_sat=("sat", "max"), occurrence=("sat", "count"))
        .reset_index()
    )

    # 4. RANKING: Prioritize things that appear often OR are very vibrant
    # This ensures the 'brown brick' or 'green pipe' makes the cut
    # grouped["rank_score"] = (grouped["total_weight"] * 10) + (grouped["max_sat"] * 2)
    grouped["rank_score"] = (grouped["total_weight"] * 10) * (grouped["max_sat"] + 5)
    top = grouped.nlargest(count, "rank_score")

    # 5. Normalize weights and pick the "purest" hex
    total_top_weight = top["total_weight"].sum()
    palette_data = []

    for _, row in top.iterrows():
        # Find the single most vibrant actual color that fell into this bucket
        best_color = (
            pool[(pool["R_B"] == row.R_B) & (pool["G_B"] == row.G_B) & (pool["B_B"] == row.B_B)]
            .nlargest(1, "sat")
            .iloc[0]
        )

        palette_data.append(
            {
                "hex": f"#{int(best_color.R):02x}{int(best_color.G):02x}{int(best_color.B):02x}",
                "weight": row["total_weight"] / total_top_weight,
            }
        )

    return palette_data


import numpy as np


def fast_game_dna(group):
    """
    Highly optimized version of get_weighted_representative_palette
    Processes a whole game group at once using vectorized operations.
    """
    # 1. Gather all C1-C8 colors into one pool instantly
    # We reshape the dataframe to have R, G, B, W columns
    r_cols = [f"C{i}_R" for i in range(1, 9)]
    g_cols = [f"C{i}_G" for i in range(1, 9)]
    b_cols = [f"C{i}_B" for i in range(1, 9)]
    w_cols = [f"C{i}_W" for i in range(1, 9)]

    # Flatten the colors: This is 100x faster than a manual loop
    r = group[r_cols].values.flatten()
    g = group[g_cols].values.flatten()
    b = group[b_cols].values.flatten()
    w = group[w_cols].values.flatten()

    # Remove NaNs
    mask = ~np.isnan(r)
    r, g, b, w = r[mask], g[mask], b[mask], w[mask]

    if len(r) == 0:
        return ""

    # 2. Vectorized Bucketing
    r_b = (r // 20 * 20).clip(0, 255)
    g_b = (g // 20 * 20).clip(0, 255)
    b_b = (b // 20 * 20).clip(0, 255)
    sat = np.max([r, g, b], axis=0) - np.min([r, g, b], axis=0)

    # 3. Use a temp dataframe for the final aggregation (the only way to group colors)
    temp = pd.DataFrame({"R": r_b, "G": g_b, "B": b_b, "W": w, "sat": sat})
    grouped = (
        temp.groupby(["R", "G", "B"]).agg(total_w=("W", "sum"), max_s=("sat", "max")).reset_index()
    )

    # Ranking
    grouped["score"] = (grouped["total_w"] * 10) * (grouped["max_s"] + 5)
    top = grouped.nlargest(8, "score")

    # Normalize weights
    total_w = top["total_w"].sum()
    return "|".join(
        [
            f"#{int(row.R):02x}{int(row.G):02x}{int(row.B):02x},{row.total_w / total_w:.3f}"
            for row in top.itertuples()
        ]
    )
