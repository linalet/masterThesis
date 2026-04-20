import os
import streamlit as st
import pandas as pd
import plotly.express as px
import helper_functions as helper
import random

# --- CONFIG & STYLING ---
st.set_page_config(
    layout="wide", page_title="Evolution of Color and Art Styles in Video Game Design"
)

baseFontSize = "23px"
st.markdown(
    """
    <style>
    /* 1. Make the Label (the title above the slider/selectbox) bigger */
    [data-testid="stWidgetLabel"] p {
        font-size: 22px !important;
        font-weight: 600 !important;
        color: ##bec4eb;
    }

    /* 2. Make the text INSIDE the Selectbox bigger */
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        font-size: 18px !important;
    }

    /* 3. Make the slider values/steps bigger */
    [data-testid="stTickBarMinMax"], [data-testid="stTickBar"] {
        font-size: 16px !important;
    }
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


search_metadata = get_summary("search_metadata.parquet")
decades_list = sorted(search_metadata["Decade"].unique().tolist())
custom_style_order = [
    "Global",
    "Realism: Photoreal",
    "Realism: Stylized",
    "Stylization: Cartoon",
    "Stylization: Illustrative",
    "Stylization: Pixel Art",
    "Stylization: Material-Based",
    "Abstraction: Minimalist",
    "Abstraction: Symbolic",
]
unclassified_labels = ["Unclassified", "Unclassified 2D", "Unclassified 3D"]
if st.session_state.get("trigger_nav"):
    st.session_state["page_selection"] = "Individual Game Palette"
    st.session_state["trigger_nav"] = False

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🎮 Game Color Analytics")
page = st.sidebar.radio(
    "Analysis Tabs",
    [
        "Project Overview",
        "Art Style Popularity",
        "Color through Decades",
        "Genre Timelines",
        "Theme Timelines",
        "Game Developer Profile",
        "Individual Game Palette",
    ],
    key="page_selection",
)
if st.sidebar.button("🎲 Random Game"):
    random_game = search_metadata["Unique_ID"].sample(1).iloc[0]
    st.session_state["search_query"] = random_game
    st.session_state["trigger_nav"] = True
    st.rerun()
if page == "Project Overview":
    st.title(
        "Exploring and Visualizing the Evolution of Color",
        text_alignment="center",
    )
    st.title(
        "and Art Styles in Video Game Design",
        text_alignment="center",
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.header("🧬 The Research Goals")
        st.write("""
                 Color and art styles play a crucial role in video games. 
                 Color can set the mood, guide the player, identify game objects, 
                 and therefore influence both the aesthetics and gameplay.
                 The rise in the use of game engines led to a certain uniformization
                 of color and art style choices.
        """)
        st.write("""
                 This thesis aims to explore
                 how the use of colors and art styles in video games changed over time by
                 providing an analysis of the collected data,
                 vizualizing the data and allowing for exploration of the collected data.
        """)
        url = "https://www.igdb.com"
        st.write("""
                 I have collected all my data from [IGDB.com](%s), which is currently the largest video game database in the world.
        """)
    with col2:
        st.header("⚙️ Research Questions")
        st.info("""        
        **Research Questions:**
        * **Q1:** How have the distributions of art styles and dominant color palettes evolved from 1950 to 2026
        * **Q2:** How effectively do aggregated "Decade Palettes" communicate the aesthetic identity of different eras?
        * **Q3:** How do genre-specific color identities evolve over decades?
                """)

    st.divider()

    st.header("🏷️ Art Style Taxonomy & Classification Logic")
    st.write(
        """
            I have developed my own game art style taxonomy for the purposes of this thesis. 
            Games are divided into 3 main categories: **Realism**, **Stylization**, and **Abstraction**.
            They are further divided into sub-categories based on keywords used to describe the game. Read more below for the detailed classification logic and examples.
            """
    )

    # for branch, styles in helper.taxonomy_data.items():
    #     st.subheader(f"{branch}")

    #     for style_name, info in styles.items():
    #         st.markdown(
    #             f"#### {style_name}",
    #             unsafe_allow_html=True,
    #         )
    #         st.markdown(f"**Aesthetic Intent:** {info['description']}")
    #         kw_html = " ".join([f"`{k}`" for k in info["keywords"]])
    #         st.markdown(f"**Keywords:** {kw_html}")

    #         cols = st.columns(3)
    #         for i, game_ref in enumerate(info["example_games"]):
    #             if i >= 3:
    #                 break
    #             with cols[i]:
    #                 # match = df[df["Unique_ID"] == game_ref["id"]]
    #                 match = search_metadata[
    #                     search_metadata["Unique_ID"].str.lower() == game_ref["id"].lower()
    #                 ]
    #                 if not match.empty:
    #                     idx = game_ref["shot_index"]
    #                     if idx >= len(match):
    #                         idx = 0

    #                     target_row = match.iloc[idx]
    #                     st.image(target_row["Screenshot"], width="stretch")
    #                     st.caption(f"🎮 **{target_row['Game']}** ({int(target_row['Year'])})")
    #                 else:
    #                     st.info(f"Image for {game_ref['id']} not found.")
    # st.divider()

    # st.subheader("⚠️ Disclaimer on Classification Accuracy")
    # st.write("""Since the keywords used to classify games are added to IGDB by the users, they are not always accurate or consistent.
    #         The automated assignment is often incorrect, but it is the only viable option available with my current resources.
    #         I have manually classified around 300 games to ensure some level of accuracy, however, it is only a fraction (0.1%) of the total dataset.
    #         Art is subjective and complex, so my opinion may not always be correct.
    #         Some games can fit into multiple categories, such as *Worse Than Death (2019)*, which could be both **Stylization: Pixel Art** and **Stylization: Illustrative**.""")
    # col1, col2 = st.columns(2)
    # with col1:
    #     st.image(
    #         df[df["Unique_ID"] == "worse than death (2019) [benjamin rivers]"].iloc[0][
    #             "Screenshot"
    #         ],
    #         width="stretch",
    #     )
    # with col2:
    #     st.image(
    #         df[df["Unique_ID"] == "worse than death (2019) [benjamin rivers]"].iloc[4][
    #             "Screenshot"
    #         ],
    #         width="stretch",
    #     )
    # st.divider()

    # st.subheader("📖 What do I do now?")
    # st.write("""
    #     If you cannot see the side menu and the tabs inside, press the arrows ⏩ in the top left corner.
    #     Navigate through the various tabs to explore the data and discover insights into the evolution of color and art styles in video games.
    # """)
    # st.write("""##### 🤔What do the tabs mean?""")
    # st.markdown("""
    # 1. **Art Style Popularity:** View the popularitty of specific styles over time.
    # 2. **Color through Decades:** See how the industry's average palette has shifted.
    # 3. **Genre Timelines:** Explore how color trends differ across genres.
    # 4. **Theme Timelines:** Explore how color trends differ across themes.
    # 3. **Game Developer Profile:** Explore game studio's most common art styles and colors.
    # 4. **Individual Game Palette:** Deep-dive into a specific game and look at its screenshots.
    # """)

elif page == "Art Style Popularity":
    st.header("📈 Art Style Popularity through Time")
    st.write("""
        This graph shows the division of art styles over time. 
        It shows how many percent of the successfully classified games each style represents in a given year.
        Another graph showing the classification success rate is shown below.
        """)

    st.subheader("Style Distribution by Year")
    pop_df = get_summary("summary_style_popularity.parquet")
    fig = px.bar(
        pop_df,
        x="Year",
        y="Percentage",
        color="Art_Style",
        height=600,
        category_orders={"Art_Style": custom_style_order},
        barmode="stack",
    )
    fig.update_layout(
        yaxis=dict(
            range=[0, 100],
            title_font=dict(size=22),
            tickfont=dict(size=20),
        ),
        xaxis=dict(
            range=[1950, 2026],
            title_font=dict(size=22),
            tickfont=dict(size=20),
        ),
        legend=dict(
            title="Art Styles",
            font=dict(size=20),
            title_font=dict(size=24),
            itemsizing="constant",
        ),
        legend_title_side="top center",
    )
    st.plotly_chart(fig, width="stretch")
    st.info(
        """ 💡TOOL TIP: Hover over the graph to see exact percentages for each style in a given year. 
        You can zoom in and out, and pan over the graph using the icons above the legend.
        You can select which styles to show by clicking on the legend items. Use autoscale to reset the zoom sfter picking the styles."""
    )
    st.divider()

    st.subheader("📈% of Games Categorized by Decade")
    success_df = get_summary("summary_success_rate.parquet")
    fig2 = px.bar(success_df, x="Decade", y="Rate")
    fig2.update_layout(
        yaxis=dict(
            range=[0, 100],
            title_font=dict(size=26),
            tickfont=dict(size=22),
        ),
        xaxis=dict(
            title_font=dict(size=26),
            tickfont=dict(size=22),
        ),
    )
    st.plotly_chart(fig2, width="stretch")

elif page == "Color through Decades":
    st.header("🎨 Color through Decades")
    st.subheader("Dominant colors of each decade (Global)")

    decade_summary = get_summary("summary_decades.parquet")

    for dec in decades_list:
        row = decade_summary[
            (decade_summary["Decade"] == dec) & (decade_summary["Art_Style"] == "Global")
        ]

        if not row.empty:
            palette_str = row.iloc[0]["Palette"]
            game_count = row.iloc[0]["Count"]
            label, col_strip = st.columns([1, 7])
            formatted_count = f"{game_count:,}".replace(",", " ")
            label.write(f"### {dec}s\n({formatted_count} games)")
            with col_strip:
                helper.draw_color_strip(palette_str)
        else:
            # debugging
            st.write(f"*(No data for {dec}s)*")

    st.divider()

    st.subheader("Dominant colors in a decade by art style")
    col_decade, col_style = st.columns([3, 1])
    sel_dec = col_decade.select_slider("Select Decade", options=decades_list)

    available_styles = sorted(
        decade_summary[decade_summary["Decade"] == sel_dec]["Art_Style"].unique().tolist()
    )

    sel_style = col_style.selectbox(
        "Select Art Style",
        available_styles,
    )

    combo_data = decade_summary[
        (decade_summary["Decade"] == sel_dec) & (decade_summary["Art_Style"] == sel_style)
    ]

    if not combo_data.empty:
        helper.draw_color_strip(combo_data.iloc[0]["Palette"], height="50px")

        st.subheader(f"Randomized examples from {sel_style} in the {sel_dec}s")
        st.write("Games may be categorized incorrectly, due to the use of user generated keywords")
        samples = search_metadata[
            (search_metadata["Decade"] == sel_dec) & (search_metadata["Art_Style"] == sel_style)
        ]
        if not samples.empty:
            img_cols = st.columns(4)
            sample_hits = samples.sample(min(4, len(samples)))
            for i, (idx, s_row) in enumerate(sample_hits.iterrows()):
                with img_cols[i % 4]:
                    st.image(s_row["Screenshot"], width="stretch")
                    st.markdown(
                        f"<div style='font-size:14px; text-align:center; color:gray; line-height:1.2; margin-top:5px;'>"
                        f"<b>{s_row['Game'].title()}</b><br>({s_row['Year']})"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info(
                "🎨 Data is being used for palette calculation, but no 'Safe for Work' screenshots are available to display for this selection."
            )
    else:
        st.info("🎨 no screenshots are available to display for this selection.")

elif page in ["Genre Timelines", "Theme Timelines"]:
    mode = "Genre" if "Genre" in page else "Theme"
    st.header(f"🎨 {mode}-Specific Color Evolution")
    st.info("**💡TOOL TIP**: Click the 🔍 tab to expand and see year-by-year breakdowns")
    st.info("💡Hover mouse over the colors in the breakdown to see their hex codes")

    timeline_df = get_summary(f"summary_{mode.lower()}s.parquet")
    items = sorted(timeline_df["Item"].unique())
    sel_item = st.selectbox(f"Select a {mode}", items)

    item_data = timeline_df[timeline_df["Item"] == sel_item].sort_values("Time")
    item_decades = sorted(item_data[item_data["Type"] == "Decade"]["Time"].unique())

    if item_decades:
        for dec in item_decades:
            dec_row = item_data[(item_data["Type"] == "Decade") & (item_data["Time"] == dec)]

            decade_info, color_strip = st.columns([1, 8])
            with decade_info:
                st.write(f"{dec}s")
                st.write("Art style")
            representative_palette = dec_row.iloc[0]["Palette"]
            with color_strip:
                helper.draw_color_strip(representative_palette, height="60px")

            with st.expander(f"🔍 See year-by-year breakdown for the {dec}s"):
                year_data = item_data[
                    (item_data["Type"] == "Year")
                    & (item_data["Time"] >= dec)
                    & (item_data["Time"] < dec + 10)
                ].sort_values("Time")

                for _, row in year_data.iterrows():
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.write(f"**{row['Time']}**")
                        st.caption(f"_{row['Top_Style']}_")
                    with col2:
                        helper.draw_color_strip(row["Palette"], height="30px")

# --- SECTION 5: DEVELOPERS ---
elif page == "Section 5: Developer Profile":
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
elif page == "Section 6: Individual Game Palette":
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
