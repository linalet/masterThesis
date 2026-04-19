import os
import streamlit as st
import pandas as pd
import plotly.express as px
import helper_functions as helper
import random

# --- CONFIG & STYLING ---
st.set_page_config(layout="wide", page_title="Evolution of Color and Art Styles")

st.markdown(
    """
    <style>
    [data-testid="stWidgetLabel"] p { font-size: 20px !important; font-weight: 600; color: #bec4eb; }
    .color-box { height: 50px; border-radius: 4px; margin: 2px; }
    .mini-color { height: 20px; width: 100%; border-radius: 2px; }
    </style>
""",
    unsafe_allow_html=True,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")


# --- DATA LOADING (LAZY) ---
@st.cache_data
def get_summary(filename):
    return pd.read_parquet(os.path.join(DATA_PATH, filename))


# Main Search Index for Section 6 and Global Lists
search_metadata = get_summary("search_metadata.parquet")
decades_list = sorted(search_metadata["Decade"].unique().tolist())
styles_list = [
    "Realism: Photoreal",
    "Realism: Stylized",
    "Stylization: Cartoon",
    "Stylization: Illustrative",
    "Stylization: Pixel Art",
    "Stylization: Material-Based",
    "Abstraction: Minimalist",
    "Abstraction: Symbolic",
]

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🎮 Game Color Analytics")
section = st.sidebar.radio(
    "Go to:",
    [
        "Section 1: Art Style Popularity",
        "Section 2: Color through Decades",
        "Section 3: Genre Timelines",
        "Section 4: Theme Timelines",
        "Section 5: Developer Profile",
        "Section 6: Individual Game Palette",
    ],
)

# --- SECTION 1: POPULARITY ---
if section == "Section 1: Art Style Popularity":
    st.header("📈 Art Style Popularity (1950-2026)")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Style Distribution by Year")
        pop_df = get_summary("summary_style_popularity.parquet")
        fig = px.bar(pop_df, x="Year", y="Percentage", color="Art_Style", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("% of Games Categorized by Decade")
        success_df = get_summary("summary_success_rate.parquet")
        fig2 = px.bar(success_df, x="Decade", y="Rate", labels={"Rate": "Categorization %"})
        st.plotly_chart(fig2, use_container_width=True)

# --- SECTION 2: DECADE VIBES ---
elif section == "Section 2: Color through Decades":
    st.header("⏳ Color through Decades")
    decade_summary = get_summary("summary_decades.parquet")

    # Global Decade Strips
    st.subheader("The Decade Color Strip")
    for dec in decades_list:
        row = decade_summary[
            (decade_summary["Decade"] == dec) & (decade_summary["Art_Style"] == "Global")
        ]
        if not row.empty:
            cols = st.columns(10)
            colors = row.iloc[0]["Palette"].split("|")
            for i, c in enumerate(colors[:10]):
                cols[i].markdown(
                    f'<div class="color-box" style="background-color:{c};"></div>',
                    unsafe_allow_html=True,
                )
            st.caption(f"**{dec}s**")

    st.divider()

    # Specific Combo
    c1, c2 = st.columns([1, 3])
    sel_dec = c1.select_slider("Select Decade", options=decades_list)
    sel_style = c1.selectbox("Select Art Style", styles_list)

    combo_data = decade_summary[
        (decade_summary["Decade"] == sel_dec) & (decade_summary["Art_Style"] == sel_style)
    ]

    if not combo_data.empty:
        p_cols = c2.columns(10)
        for i, c in enumerate(combo_data.iloc[0]["Palette"].split("|")):
            p_cols[i].markdown(
                f'<div class="color-box" style="background-color:{c};"></div>',
                unsafe_allow_html=True,
            )

        # 4 Random Screenshots (Pre-filtered from search_metadata for speed)
        samples = search_metadata[
            (search_metadata["Decade"] == sel_dec) & (search_metadata["Art_Style"] == sel_style)
        ]
        if not samples.empty:
            img_cols = st.columns(4)
            sample_hits = samples.sample(min(4, len(samples)))
            for i, (idx, s_row) in enumerate(sample_hits.iterrows()):
                img_cols[i].image(s_row["Screenshot"], caption=s_row["Game"])

# --- SECTION 3 & 4: TIMELINES ---
elif section in ["Section 3: Genre Timelines", "Section 4: Theme Timelines"]:
    mode = "Genres" if "Genre" in section else "Themes"
    st.header(f"📅 {mode} Timeline")

    timeline_df = get_summary(f"summary_{mode.lower()}.parquet")
    items = sorted(timeline_df["Item"].unique())
    sel_item = st.selectbox(f"Select a {mode[:-1]}", items)

    item_data = timeline_df[timeline_df["Item"] == sel_item].sort_values("Time")

    for _, row in item_data.iterrows():
        with st.expander(f"🖼️ {row['Time']} — (Top Style: {row['Top_Style']})"):
            t_cols = st.columns(10)
            for i, c in enumerate(row["Palette"].split("|")):
                t_cols[i].markdown(
                    f'<div class="color-box" style="background-color:{c};"></div>',
                    unsafe_allow_html=True,
                )

# --- SECTION 5: DEVELOPERS ---
elif section == "Section 5: Developer Profile":
    st.header("🏢 Game Developer Profile")
    studio_summary = get_summary("summary_studios.parquet")

    tab1, tab2, tab3 = st.tabs(["Top 50 All-Time", "Decade Specific", "Head to Head"])

    with tab1:
        dev_choice = st.selectbox("Pick Developer", studio_summary["Studio"].tolist())
        dev_row = studio_summary[studio_summary["Studio"] == dev_choice].iloc[0]

        c1, c2 = st.columns([2, 1])
        pal_cols = c1.columns(10)
        for i, c in enumerate(dev_row["Palette"].split("|")):
            pal_cols[i].markdown(
                f'<div class="color-box" style="background-color:{c};"></div>',
                unsafe_allow_html=True,
            )

        fig = px.pie(
            names=dev_row["Style_Distribution"].keys(),
            values=dev_row["Style_Distribution"].values(),
            title="Art Style Distribution",
        )
        c2.plotly_chart(fig)

    # Note: tab2 and tab3 would implement similar logic using a decade-filtered version of the studio_summary

# --- SECTION 6: INDIVIDUAL GAME ---
elif section == "Section 6: Individual Game Palette":
    st.header("🎮 Individual Game Palette")

    game_query = st.selectbox("Search for a game...", search_metadata["Unique_ID"].tolist())

    if game_query:
        game_data = search_metadata[search_metadata["Unique_ID"] == game_query].iloc[0]

        # Weighted Top 8
        st.subheader(f"Weighted Palette: {game_data['Game']}")
        p_cols = st.columns(8)
        game_pal = game_data["Color_palette"].split("|")
        for i, c in enumerate(game_pal[:8]):
            p_cols[i].markdown(
                f'<div class="color-box" style="background-color:{c};"></div>',
                unsafe_allow_html=True,
            )

        # Comparison logic
        decade_avg = get_summary("summary_decades.parquet")
        # Logic to compare game_data['saturation'] vs decade_avg for decade
        st.info(
            f"This game's saturation is being compared to the {game_data['Decade']}s average..."
        )

        st.divider()
        st.subheader("Screenshot Breakdown")

        # Real-time load of screenshots for this specific game
        all_shots = get_summary("color_analytics.parquet")
        game_shots = all_shots[all_shots["Unique_ID"] == game_query]

        shot_cols = st.columns(len(game_shots))
        for i, (_, shot) in enumerate(game_shots.iterrows()):
            with shot_cols[i]:
                st.image(shot["Screenshot"])
                # Mini palette top 5 (R,G,B columns)
                mini_cols = st.columns(5)
                for j in range(1, 6):
                    r, g, b = shot[f"C{j}_R"], shot[f"C{j}_G"], shot[f"C{j}_B"]
                    hex_c = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                    mini_cols[j - 1].markdown(
                        f'<div class="mini-color" style="background-color:{hex_c};"></div>',
                        unsafe_allow_html=True,
                    )
