import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set page config for a wider layout
st.set_page_config(layout="wide", page_title="Video Game Color Thesis")


# --- 1. DATA LOADING & ACADEMIC TAXONOMY ---
@st.cache_data
def load_data():
    # Adjusted path logic to find your CSV
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data/test_game_data.csv")

    if not os.path.exists(csv_path):
        st.error(f"CSV not found at {csv_path}. Please check your file structure.")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)

    # Clean strings and handle missing metadata
    for col in ["Genres", "Themes", "Keywords", "Developers", "Game"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    # Clean Year data
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)

    def classify_taxonomy(row):
        """
        Implements Level 1 (Intent) and Level 2 (Technique)
        based on Cho et al. and Wattanasoontorn.
        """
        text = f"{row['Keywords']} {row['Themes']} {row['Genres']}".lower()

        # I. REALISM (Intent)
        if any(w in text for w in ["photoreal", "ray-tracing", "pbr", "realistic"]):
            return "Realism: High-Fidelity"
        if any(w in text for w in ["illusionism", "fantasy realism", "televisual"]):
            return "Realism: Stylized Realism"

        # II. STYLIZATION (Intent)
        if any(w in text for w in ["watercolor", "hand-painted", "comic", "cel-shade"]):
            return "Stylization: Illustrative"
        if any(w in text for w in ["anime", "manga", "chibi", "cartoon"]):
            return "Stylization: Caricature"
        if any(w in text for w in ["pixel", "8-bit", "16-bit", "low-poly", "voxel"]):
            return "Stylization: Retro-Tech"
        if any(w in text for w in ["claymation", "papercraft", "puppet"]):
            return "Stylization: Material-Based"

        # III. ABSTRACTION (Intent)
        if any(w in text for w in ["flat art", "vector", "silhouette", "geometric"]):
            return "Abstraction: Minimalist"
        if any(w in text for w in ["text-based", "experimental", "psychedelic"]):
            return "Abstraction: Symbolic"

        # Fallback to avoid 'Non-Classified' labels in UI
        if row["Year"] < 1980:
            return "Abstraction: Minimalist"
        return "Realism: Stylized Realism"

    # Pre-calculate metrics for thesis analysis
    df["Art_Style"] = df.apply(classify_taxonomy, axis=1)
    df["saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )

    return df[df["Year"] > 1950].copy()


df = load_data()


# --- 2. THE REPRESENTATIVE PALETTE ENGINE ---
def get_representative_palette(yr_data, count=10):
    """
    Groups colors and boosts distinct hues while preserving
    muted tones for historical accuracy.
    """
    # Create copies to avoid SettingWithCopy warnings
    data = yr_data.copy()

    # Bucket colors to find common themes
    for c in ["R", "G", "B"]:
        data[f"{c}_B"] = (data[f"C1_{c}"] // 30 * 30).clip(0, 255)

    # Re-calculate saturation for the subset
    data["sat"] = data[["C1_R", "C1_G", "C1_B"]].max(axis=1) - data[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )

    grouped = (
        data.groupby(["R_B", "G_B", "B_B"])
        .agg(total_count=("sat", "count"), avg_sat=("sat", "mean"))
        .reset_index()
    )

    # Weighting logic: prioritize color over pure black/grey
    grouped["rank_score"] = grouped["total_count"] * (grouped["avg_sat"] + 15)
    top = grouped.nlargest(count, "rank_score")

    return [f"#{int(r):02x}{int(g):02x}{int(b):02x}" for r, g, b in zip(top.R_B, top.G_B, top.B_B)]


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


# --- 3. UI LAYOUT ---
st.sidebar.title("Thesis Dashboard")
page = st.sidebar.radio(
    "Analysis Tabs", ["Market Trends (%)", "Color Archetypes", "Studio DNA", "Genre Timelines"]
)

if page == "Color Archetypes":
    st.header("🎨 Palette Archetypes & Technological Milestones")

    # Show mathematical proof of color shifts
    render_saturation_heatmap(df)

    st.subheader("The Decade Color Pillar")
    st.write("Evolution of the dominant industry palette alongside tech milestones.")

    milestones = {
        1970: "🕹️ First Arcades (PONG)",
        1980: "🎮 8-Bit Era (NES/Master System)",
        1990: "📐 The 3D Shift (PS1/N64)",
        2000: "🎞️ Cinematic Realism (PS2/Xbox)",
        2010: "💡 Modern Lighting (DirectX 11)",
        2020: "✨ Ray Tracing & HDR Era",
    }

    # Generate the representative bars
    for dec in [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]:
        dec_df = df[(df["Year"] >= dec) & (df["Year"] < dec + 10)]
        if not dec_df.empty:
            pal = get_representative_palette(dec_df, count=12)

            c1, c2, c3 = st.columns([1, 2, 6])
            c1.write(f"### {dec}s")
            c2.info(milestones.get(dec, "Evolutionary Period"))

            with c3:
                html = '<div style="display: flex; height: 50px; border-radius: 8px; overflow: hidden; border: 1px solid #333; margin-bottom: 25px;">'
                for color in pal:
                    html += f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

elif page == "Market Trends (%)":
    st.header("📈 Art Style Market Share (Cho et al. Taxonomy)")
    # Calculate percentages for the area chart
    style_counts = df.groupby(["Year", "Art_Style"]).size().reset_index(name="Count")
    year_totals = df.groupby("Year").size().reset_index(name="Total")
    perc_df = style_counts.merge(year_totals, on="Year")
    perc_df["Percentage"] = (perc_df["Count"] / perc_df["Total"]) * 100

    fig = px.area(
        perc_df,
        x="Year",
        y="Percentage",
        color="Art_Style",
        color_discrete_sequence=px.colors.qualitative.Safe,
        height=600,
    )
    fig.update_yaxes(range=[0, 100])
    fig.update_xaxes(range=[1950, 2026])
    st.plotly_chart(fig, use_container_width=True)

elif page == "Studio DNA":
    st.header("🏢 Studio Visual Fingerprints")
    # Identify top developers for the thesis
    top_studios = df["Developers"].value_counts().nlargest(15).index.tolist()
    sel_studio = st.selectbox("Select Developer to Analyze", top_studios)

    if sel_studio:
        s_df = df[df["Developers"] == sel_studio]
        st.write(f"### {sel_studio.title()} Style Distribution")

        col_a, col_b = st.columns(2)
        with col_a:
            st.plotly_chart(px.pie(s_df, names="Art_Style", hole=0.4), use_container_width=True)
        with col_b:
            studio_pal = get_representative_palette(s_df, count=10)
            st.write("#### Core Palette")
            # Display vertical color list
            for c in studio_pal:
                st.markdown(
                    f'<div style="background-color:{c}; padding:10px; border-radius:4px; color:white; font-family:monospace; margin-bottom:2px;">{c}</div>',
                    unsafe_allow_html=True,
                )

elif page == "Genre Timelines":
    st.header("📅 Historical Color Strip")
    # Filter by genre to see evolution
    all_genres = sorted(list(set(df["Genres"].str.split("|").explode().str.strip().unique())))
    sel_genre = st.selectbox("Select Genre", [g for g in all_genres if g])

    g_df = df[df["Genres"].str.contains(sel_genre, case=False, na=False)]

    for yr in sorted(g_df["Year"].unique(), reverse=True)[:30]:
        y_data = g_df[g_df["Year"] == yr]
        pal = get_representative_palette(y_data, count=8)

        c1, c2, c3 = st.columns([1, 2, 6])
        c1.write(f"**{yr}**")
        # Display the most common Style for that year
        c2.caption(f"Style: {y_data['Art_Style'].mode()[0]}")
        with c3:
            html = '<div style="display: flex; height: 20px; border-radius: 4px; overflow: hidden; margin-bottom: 8px; border: 1px solid #444;">'
            for color in pal:
                html += f'<div style="background-color:{color}; flex:1;"></div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
