import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. CONFIGURATION & TAXONOMY ---
st.set_page_config(page_title="Game Art Style & Color Evolution", layout="wide")

# Your Taxonomy from the snippets
SUB_CATEGORY_MAP = {
    "Realism": {
        "Photorealistic": ["photorealistic", "photorealism", "high-fidelity"],
        "Semi-Realistic": ["semi-realistic", "illusionism", "televisualism"],
        "3D Realism": ["3d realism", "realistic"],
    },
    "Stylized & Cartoon": {
        "Cel-Shaded": ["cel-shaded", "anime", "manga"],
        "Cartoon/Comic": ["cartoon", "comic", "caricature", "exaggerated"],
        "Hand-Drawn": ["hand-drawn", "stylized"],
    },
    "Retro & Tech-Driven": {
        "Pixel Art (8/16-bit)": ["pixel art", "8-bit", "16-bit", "pixelated"],
        "Voxel": ["voxel", "blocky", "lego"],
        "Retro Graphics": ["retro graphics"],
    },
    "Abstract & Minimal": {
        "Minimalism": ["minimalist", "minimalism", "simplified"],
        "Flat/Vector": ["flat art", "flat design", "vector art"],
        "Silhouette": ["silhouette", "text-based"],
    },
    "Atmospheric & Mood": {
        "B&W/Monochrome": ["noir", "monochrome", "black and white", "monochromatic"],
        "Neon/Bright": ["neon", "vibrant", "bright", "psychedelic"],
        "Gritty/Dark": ["gritty", "dark", "gloomy"],
    },
}


# --- 2. DATA LOADING & PROCESSING ---
@st.cache_data
def load_and_process_data():
    df = pd.read_csv("data/game_data.csv")

    # Apply Taxonomy Classification
    def classify_sub_styles(row):
        text = f"{row.get('Keywords', '')} {row.get('Themes', '')} {row.get('Game', '')}".lower()
        found_subs = []
        for high_level, subs in SUB_CATEGORY_MAP.items():
            for sub_name, keywords in subs.items():
                if any(word in text for word in keywords):
                    found_subs.append(f"{high_level}: {sub_name}")
        return "|".join(found_subs) if found_subs else "Unclassified"

    df["Sub_Styles_Full"] = df.apply(classify_sub_styles, axis=1)

    # Generate Hex colors for UI display
    def to_hex(r, g, b):
        if pd.isna(r):
            return "#FFFFFF"
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    df["C1_Hex"] = df.apply(lambda r: to_hex(r.C1_R, r.C1_G, r.C1_B), axis=1)
    return df


df = load_and_process_data()

# --- 3. SIDEBAR FILTERS ---
st.sidebar.title("Thesis Exploration")
safe_mode = st.sidebar.checkbox("Safe Mode (Hide NSFW)", value=True)

years = st.sidebar.slider("Year Range", int(df.Year.min()), int(df.Year.max()), (2016, 2025))

# Perspective Multi-select (Restored)
all_persp = sorted(list(set("|".join(df["Perspectives"].fillna("Unknown")).split("|"))))
selected_persp = st.sidebar.multiselect("Player Perspective", all_persp)

# Filter Dataset
filtered_df = df[(df.Year >= years[0]) & (df.Year <= years[1])]
if selected_persp:
    filtered_df = filtered_df[
        filtered_df["Perspectives"].apply(lambda x: any(p in str(x) for p in selected_persp))
    ]

# NSFW Visibility Logic
if safe_mode:
    display_df = filtered_df[filtered_df["Is_NSFW"] == 0]
else:
    display_df = filtered_df

# --- 4. APP TABS ---
tab1, tab2, tab3 = st.tabs(["Color Trends", "Art Style Taxonomy", "Data Explorer"])

# --- TAB 1: COLOR TRENDS ---
with tab1:
    st.header("Saturation & Luminance Evolution")
    st.write(
        "Exploration of how visual technology (PBR, RTX) affects game brightness and color intensity."
    )

    chart_type = st.radio("Group by:", ["Year", "Decade", "Perspectives"])

    # Calculate means
    trend_data = (
        filtered_df.groupby(chart_type)[["Avg_Saturation", "Avg_Luminance"]].mean().reset_index()
    )

    fig = px.scatter(
        trend_data,
        x="Avg_Luminance",
        y="Avg_Saturation",
        text=chart_type,
        size_max=60,
        title=f"Color Shift by {chart_type}",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Weighted Color Barcode (Top 100 games in current view)
    st.subheader("Dominant Color Palette (Weighted)")
    barcode_df = display_df.head(100)
    fig_barcode = px.bar(
        barcode_df,
        x="Game",
        y="C1_W",
        color="C1_Hex",
        color_discrete_map="identity",
        title="Dominant Color Weight (C1_W)",
    )
    fig_barcode.update_layout(showlegend=False, xaxis_showticklabels=False)
    st.plotly_chart(fig_barcode, use_container_width=True)

# --- TAB 2: ART STYLE TAXONOMY ---
with tab2:
    st.header("Art Style Composition")

    # Explode styles for counting
    exploded_styles = filtered_df[filtered_df["Sub_Styles_Full"] != "Unclassified"].copy()
    exploded_styles["Sub_Styles_Full"] = exploded_styles["Sub_Styles_Full"].str.split("|")
    exploded_styles = exploded_styles.explode("Sub_Styles_Full")
    exploded_styles[["High_Level", "Sub_Style"]] = exploded_styles["Sub_Styles_Full"].str.split(
        ": ", expand=True
    )

    # 100% Stacked Area Chart
    style_counts = exploded_styles.groupby(["Year", "High_Level"]).size().reset_index(name="Count")
    fig_area = px.area(
        style_counts,
        x="Year",
        y="Count",
        color="High_Level",
        groupnorm="percent",
        title="Relative Popularity of Art Styles",
    )
    st.plotly_chart(fig_area, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sub-Style Distribution")
        sub_counts = exploded_styles.groupby("Sub_Style").size().reset_index(name="Count")
        st.plotly_chart(
            px.pie(sub_counts, values="Count", names="Sub_Style"), use_container_width=True
        )

    with col2:
        st.subheader("Style vs. Perspective")
        sun_df = (
            exploded_styles.groupby(["Perspectives", "High_Level"]).size().reset_index(name="Count")
        )
        st.plotly_chart(
            px.sunburst(sun_df, path=["Perspectives", "High_Level"], values="Count"),
            use_container_width=True,
        )

# --- TAB 3: DATA EXPLORER (The Gallery) ---
with tab3:
    st.header("Screenshot Gallery")
    st.info(f"Showing {len(display_df)} games matching filters. Use Sidebar for Safe Mode.")

    search = st.text_input("Search Game Name...")
    if search:
        display_df = display_df[display_df["Game"].str.contains(search, case=False)]

    cols = st.columns(4)
    for idx, row in display_df.head(40).iterrows():
        with cols[idx % 4]:
            # The Logic: NSFW is allowed in the dataset for math, but hidden in the UI gallery
            if row["Is_NSFW"] == 1 and safe_mode:
                st.image(
                    "https://placehold.co/600x400?text=NSFW+Content+Hidden",
                    caption=f"Censored: {row['Game']}",
                )
            else:
                st.image(row["Screenshot"], caption=f"{row['Game']} ({row['Year']})")
                # Show mini palette
                st.write(f"🎨 {row['C1_Hex']} | Sat: {row['Avg_Saturation']:.2f}")
