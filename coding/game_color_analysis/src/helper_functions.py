import streamlit as st
import pandas as pd
import os
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

    # I. REALISM
    if any(w in text for w in ["photoreal", "ray-tracing", "pbr", "realistic"]):
        return "Realism: High-Fidelity"  # like 0 games at all...
    if any(w in text for w in ["illusionism", "fantasy realism", "televisual"]):
        return "Realism: Stylized Realism"

    # II. STYLIZATION
    if any(w in text for w in ["watercolor", "hand-painted", "comic", "cel-shade"]):
        return "Stylization: Illustrative"
    if any(w in text for w in ["anime", "manga", "chibi", "cartoon"]):
        return "Stylization: Caricature"
    if any(w in text for w in ["pixel", "8-bit", "16-bit", "low-poly", "voxel"]):
        return "Stylization: Retro-Tech"
    if any(w in text for w in ["claymation", "papercraft", "puppet"]):
        return "Stylization: Material-Based"

    # III. ABSTRACTION
    if any(w in text for w in ["flat art", "vector", "silhouette", "geometric"]):
        return "Abstraction: Minimalist"
    if any(w in text for w in ["text-based", "experimental", "psychedelic"]):
        return "Abstraction: Symbolic"

    if any(w in text for w in ["3d", "3-D"]):
        return "Unclassified 3D"
    if any(w in text for w in ["2d", "2-D"]):
        return "Unclassified 2D"
    # if row["Year"] < 2000:
    #     return "Unknown - pixel art?"
    return "Unclassified"


def get_representative_palette(yr_data, count=10):
    data = yr_data.copy()

    # Calculate saturation for the current selection
    data["sat"] = data[["C1_R", "C1_G", "C1_B"]].max(axis=1) - data[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )

    # Bucket colors to group similar tones
    for c in ["R", "G", "B"]:
        data[f"{c}_B"] = (data[f"C1_{c}"] // 20 * 20).clip(0, 255)

    grouped = (
        data.groupby(["R_B", "G_B", "B_B"])
        .agg(total_count=("sat", "count"), avg_sat=("sat", "mean"))
        .reset_index()
    )

    # LOGIC FIX: If the average saturation is extremely low (< 10), rank by count alone.
    # This prevents black/white/grey colors from being ignored.
    if grouped["avg_sat"].mean() < 10:
        grouped["rank_score"] = grouped["total_count"]
    else:
        # For colored games, prioritize vibrant hues while still considering frequency
        grouped["rank_score"] = grouped["total_count"] * (grouped["avg_sat"] + 15)

    top = grouped.nlargest(count, "rank_score")
    return [f"#{int(r):02x}{int(g):02x}{int(b):02x}" for r, g, b in zip(top.R_B, top.G_B, top.B_B)]


def load_data():
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/game_data.csv"
    )
    df = pd.read_csv(csv_path, low_memory=False)

    for col in ["Genres", "Themes", "Keywords", "Developers", "Game"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
    # df["Developers"] = df["Developers"].fillna("").astype(str).str.lower()

    df["Developers"] = df["Developers"].apply(normalize_studio_name)
    all_devs_series = df["Developers"].str.split("|").explode().str.strip()

    top_studios_global = (
        all_devs_series[all_devs_series != ""].value_counts().nlargest(50).index.tolist()
    )
    unique_devs = sorted(all_devs_series[all_devs_series != ""].unique().tolist())

    df["Art_Style"] = df.apply(classify_taxonomy, axis=1)
    df["saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )
    df["luminance"] = (0.2126 * df["C1_R"] + 0.7152 * df["C1_G"] + 0.0722 * df["C1_B"]) / 255.0

    df["Decade"] = (df["Year"] // 10 * 10).astype(int).astype(str) + "s"

    return df[df["Year"] > 1950].copy(), unique_devs, top_studios_global


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
