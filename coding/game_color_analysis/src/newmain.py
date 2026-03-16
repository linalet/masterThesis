import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. CONFIGURATION & TAXONOMY ---
st.set_page_config(page_title="Game Art Style Evolution", layout="wide")

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

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- 2. DATA LOADING & PROCESSING ---
@st.cache_data
def load_data():
    # index_col=False prevents Column 0 from being treated as a weird index
    df = pd.read_csv(ROOT_DIR + "/data/new_game_data.csv", index_col=False)

    # --- ARROW-SAFE NUMERIC CONVERSION ---
    # Convert to float64 first, then int. This is the most stable path for PyArrow.
    numeric_to_float = ["Year", "Decade", "Is_NSFW"]
    for i in range(1, 6):
        numeric_to_float.append(f"C{i}_W")
        for chan in ["R", "G", "B"]:
            numeric_to_float.append(f"C{i}_{chan}")

    for col in numeric_to_float:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("float64")

    # --- STRING CLEANING ---
    text_cols = ["Keywords", "Themes", "Game", "Genres", "Player Perspectives"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
        else:
            df[col] = ""

    # --- CLASSIFICATION LOGIC ---
    def classify_styles(row):
        text = f"{row['Keywords']} {row['Themes']} {row['Game']} {row['Genres']}".lower()
        found = []
        for high, subs in SUB_CATEGORY_MAP.items():
            for sub_name, keywords in subs.items():
                if any(word in text for word in keywords):
                    found.append(f"{high}: {sub_name}")
        return "|".join(found) if found else "Unclassified"

    df["Style_Tag"] = [classify_styles(row) for _, row in df.iterrows()]

    # --- HEX COLOR GENERATION ---
    def to_hex(r, g, b):
        try:
            return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        except:
            return "#808080"

    df["C1_Hex"] = [to_hex(r.C1_R, r.C1_G, r.C1_B) for _, r in df.iterrows()]

    # Filter out invalid entries
    df = df[df["Year"] > 0]

    # --- THE UNIVERSAL ARROW FIX ---
    # Convert back to standard Python dict and re-create DataFrame
    # This strips 'Int64DType' and leaves standard float64/objects
    df = pd.DataFrame(df.to_dict())

    return df


df = load_data()

# --- 3. SIDEBAR FILTERS ---
st.sidebar.title("Thesis: Color & Style")
safe_mode = st.sidebar.checkbox("Safe Mode (Hide NSFW Images)", value=True)

# Year slider using calculated bounds
min_y, max_y = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider("Years", min_y, max_y, (2016, 2025))

# Perspective Filter
all_persp = sorted(list(set("|".join(df["Player Perspectives"]).split("|"))))
all_persp = [p for p in all_persp if p.strip()]  # Remove empty strings
selected_persp = st.sidebar.multiselect("Filter by Perspective", all_persp)

# Filter Dataframe
filtered_df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]

if selected_persp:
    pattern = "|".join(selected_persp)
    filtered_df = filtered_df[filtered_df["Player Perspectives"].str.contains(pattern, na=False)]

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["Visual Uniformity", "Art Style Trends", "Screenshot Explorer"])

# --- TAB 1: VISUAL UNIFORMITY ---
with tab1:
    st.header("Color Dominance & Uniformity")
    st.write("Analysis of C1_Weight (How much space the primary color occupies).")

    # Grouping
    avg_weight = filtered_df.groupby("Year")["C1_W"].mean().reset_index()

    if not avg_weight.empty:
        fig_weight = px.line(
            avg_weight, x="Year", y="C1_W", title="Average Dominance of Primary Color"
        )
        fig_weight.update_yaxes(title="Weight (0.0 - 1.0)")
        st.plotly_chart(fig_weight, use_container_width=True)

        st.divider()

        st.subheader("Uniformity by Perspective")
        fig_box = px.box(filtered_df, x="Player Perspectives", y="C1_W", points="all")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("Adjust filters to see uniformity data.")

# --- TAB 2: ART STYLE TRENDS ---
with tab2:
    st.header("Taxonomy Evolution")

    style_df = filtered_df[filtered_df["Style_Tag"] != "Unclassified"].copy()

    if not style_df.empty:
        style_df["Style_Tag"] = style_df["Style_Tag"].str.split("|")
        style_df = style_df.explode("Style_Tag")

        def safe_split(val):
            if ":" in str(val):
                parts = val.split(": ")
                return parts[0], parts[1]
            return val, "General"

        split_data = style_df["Style_Tag"].apply(safe_split)
        style_df["High_Level"] = [x[0] for x in split_data]
        style_df["Sub_Style"] = [x[1] for x in split_data]

        style_counts = style_df.groupby(["Year", "High_Level"]).size().reset_index(name="Count")

        fig_area = px.area(
            style_counts,
            x="Year",
            y="Count",
            color="High_Level",
            groupnorm="percent",
            title="Art Style Popularity (%)",
        )
        st.plotly_chart(fig_area, use_container_width=True)

        # Genre Bar
        st.subheader("Dominance by Genre")
        genre_df = filtered_df.copy()
        genre_df["Genres"] = genre_df["Genres"].str.split("|")
        genre_df = genre_df.explode("Genres")
        genre_df = genre_df[genre_df["Genres"] != ""]

        if not genre_df.empty:
            g_weight = genre_df.groupby("Genres")["C1_W"].mean().sort_values().reset_index()
            st.plotly_chart(
                px.bar(g_weight, x="C1_W", y="Genres", orientation="h"), use_container_width=True
            )
    else:
        st.info("No classified games found in this range.")

# --- TAB 3: EXPLORER ---
with tab3:
    st.header("Data Gallery")

    gallery_df = filtered_df.copy()
    if safe_mode:
        gallery_df = gallery_df[gallery_df["Is_NSFW"] == 0]

    search = st.text_input("Search Game Name")
    if search:
        gallery_df = gallery_df[gallery_df["Game"].str.contains(search, case=False)]

    st.write(f"Showing {len(gallery_df.head(80))} results.")

    cols = st.columns(4)
    for i, (idx, row) in enumerate(gallery_df.head(80).iterrows()):
        with cols[i % 4]:
            st.image(row["Screenshot"], caption=f"{row['Game']} ({int(row['Year'])})")
            st.markdown(
                f'<div style="background-color:{row["C1_Hex"]}; height:8px; width:100%;"></div>',
                unsafe_allow_html=True,
            )
            st.caption(f"C1 Weight: {row['C1_W']:.1%}")
