import os
import streamlit as st
import pandas as pd
import plotly.express as px
import helper_functions as helper
import csv

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

# path = os.path.join(
#     os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
#     # "data/final_processed_game_data.parquet",
#     "data/processed_game_data.parquet",
# )
# url = "https://drive.google.com/uc?export=download&id=1lO3ZSw-KWMC5Dw-QCknqjJE4Ug3WPI8U"

# url = "https://www.dropbox.com/scl/fi/etarsizhoelwtcabib2n2/final_processed_game_data.parquet?rlkey=1das5lwj8bg51bk4ezljr9r3b&st=wg6tcbc8&dl=1"
url = "https://www.dropbox.com/scl/fi/etarsizhoelwtcabib2n2/final_processed_game_data.parquet?rlkey=1das5lwj8bg51bk4ezljr9r3b&st=wg6tcbc8&raw=1"
df, unique_devs_list, top_50_global = helper.load_data(url)
df_safe = df[~df["is_nsfw"]].copy()
decades = sorted(list(set(df["Decade"].unique())))
custom_style_order = [
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

page = st.sidebar.radio(
    "Analysis Tabs",
    [
        "Project Overview",
        "Art Style Popularity",
        # "Style Categorizer",
        "Color through Decades",
        "Genre Timelines",
        "Theme Timelines",
        "Game Developer Profile",
        "Individual Game Palette",
    ],
    key="page_selection",
)
if st.sidebar.button("🎲 Random Game"):
    random_game = df["Unique_ID"].sample(1).iloc[0]
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

    # Detailed Taxonomy Data Structure
    taxonomy_data = {
        "1️⃣ Realism": {
            "Photoreal": {
                "description": "Visuals trying to look as realistic as possible. Can utilize physically based rendering (PBR) and high-resolution textures.",
                "keywords": [
                    "ray-tracing",
                    "pbr",
                    "realistic",
                    "4k",
                ],
                "example_games": [
                    {"id": "cyberpunk 2077 (2020) [cd projekt red]", "shot_index": 9},
                    {"id": "the last of us part ii (2020) [naughty dog]", "shot_index": 0},
                    {"id": "forza horizon 5 (2021) [playground games]", "shot_index": 0},
                ],
            },
            "Stylized": {
                "description": "Retains realistic proportions and lighting but adds artistic flair. Often mimics the look of high-end film or fantasy illustration.",
                "keywords": [
                    "cinematic",
                    "atmospheric",
                ],
                "example_games": [
                    {"id": "the sims 4 (2014) [maxis]", "shot_index": 4},
                    {"id": "portal 2 (2011) [valve]", "shot_index": 1},
                    {"id": "the witcher 3: wild hunt (2015) [cd projekt red]", "shot_index": 10},
                ],
            },
        },
        "2️⃣ Stylization": {
            "Cartoon": {
                "description": "Focuses on exaggerated proportions and vibrant colors. Often inspired by anime or cartoons.",
                "keywords": ["anime", "manga", "chibi", "cartoon"],
                "example_games": [
                    {"id": "team fortress 2 (2007) [valve]", "shot_index": 0},
                    {
                        "id": "genshin impact (2020) [Cognosphere]",
                        "shot_index": 10,
                    },
                    {"id": "super mario odyssey (2017) [nintendo]", "shot_index": 0},
                ],
            },
            "Illustrative": {
                "description": "Emphasizes the 'art'. Mimics physical media like watercolors or ink drawings.",
                "keywords": [
                    "watercolor",
                    "hand-painted",
                    "hand-drawn",
                    "sketch",
                ],
                "example_games": [
                    {"id": "machinarium (2009) [amanita design]", "shot_index": 0},
                    {"id": "ōkami (2006) [clover studio]", "shot_index": 2},
                    {"id": "don't starve (2013) [klei entertainment]", "shot_index": 0},
                ],
            },
            "Pixel Art": {
                "description": "Art style limited or inspired by the technical constraints of early gaming hardware. Uses squares.",
                "keywords": ["pixel art", "8-bit", "16-bit"],
                "example_games": [
                    {"id": "stardew valley (2016) [concernedape]", "shot_index": 0},
                    {"id": "minecraft (2011) [mojang studios]", "shot_index": 3},
                    {"id": "undertale (2015) [tobyfox]", "shot_index": 3},
                ],
            },
            "Material-Based": {
                "description": "Games designed to look like they are constructed from physical materials. Often uses stop-motion.",
                "keywords": [
                    "claymation",
                    "papercraft",
                    "stop-motion",
                    "felt",
                ],
                "example_games": [
                    {"id": "it takes two (2021) [hazelight studios]", "shot_index": 0},
                    {"id": "the neverhood (1996) [the neverhood, inc.]", "shot_index": 2},
                    {"id": "samorost 3 (2016) [amanita design]", "shot_index": 3},
                ],
            },
        },
        "3️⃣ Abstraction": {
            "Minimalist": {
                "description": "Reduces visuals to only essential elements. Uses clean lines, silhouettes, and simple shapes.",
                "keywords": ["silhouette", "geometric", "minimalist"],
                "example_games": [
                    {"id": "superhot (2016) [ea]", "shot_index": 0},
                    {"id": "voxel blast (2015) [ceiba software & arts]", "shot_index": 1},
                    {"id": "limbo (2010) [ea]", "shot_index": 4},
                ],
            },
            "Symbolic": {
                "description": "Color and shape represent ideas or mechanics. Also includestext-based and audio-based games with limited visual art.",
                "keywords": [
                    "text-based",
                    "experimental",
                    "psychedelic",
                    "ascii",
                ],
                "example_games": [
                    {
                        "id": "the hitchhiker's guide to the galaxy (1984) [infocom]",
                        "shot_index": 0,
                    },
                    {"id": "thomas was alone (2012) [bithell games]", "shot_index": 2},
                    {"id": "dark echo (2015) [rac7 games]", "shot_index": 1},
                ],
            },
        },
    }

    for branch, styles in taxonomy_data.items():
        st.subheader(f"{branch}")

        for style_name, info in styles.items():
            st.markdown(
                f"#### {style_name}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**Aesthetic Intent:** {info['description']}")
            kw_html = " ".join([f"`{k}`" for k in info["keywords"]])
            st.markdown(f"**Keywords:** {kw_html}")

            cols = st.columns(3)
            for i, game_ref in enumerate(info["example_games"]):
                if i >= 3:
                    break
                with cols[i]:
                    # match = df[df["Unique_ID"] == game_ref["id"]]
                    match = df[df["Unique_ID"].str.lower() == game_ref["id"].lower()]
                    if not match.empty:
                        idx = game_ref["shot_index"]
                        if idx >= len(match):
                            idx = 0

                        target_row = match.iloc[idx]
                        st.image(target_row["Screenshot"], width="stretch")
                        st.caption(f"🎮 **{target_row['Game']}** ({int(target_row['Year'])})")
                    else:
                        st.info(f"Image for {game_ref['id']} not found.")
    st.divider()

    st.subheader("⚠️ Disclaimer on Classification Accuracy")
    st.write("""Since the keywords used to classify games are added to IGDB by the users, they are not always accurate or consistent.
            The automated assignment is often incorrect, but it is the only viable option available with my current resources.
            I have manually classified around 300 games to ensure some level of accuracy, however, it is only a fraction (0.1%) of the total dataset.
            Art is subjective and complex, so my opinion may not always be correct. 
            Some games can fit into multiple categories, such as *Worse Than Death (2019)*, which could be both **Stylization: Pixel Art** and **Stylization: Illustrative**.""")
    col1, col2 = st.columns(2)
    with col1:
        st.image(
            df[df["Unique_ID"] == "worse than death (2019) [benjamin rivers]"].iloc[0][
                "Screenshot"
            ],
            width="stretch",
        )
    with col2:
        st.image(
            df[df["Unique_ID"] == "worse than death (2019) [benjamin rivers]"].iloc[4][
                "Screenshot"
            ],
            width="stretch",
        )
    st.divider()

    st.subheader("📖 What do I do now?")
    st.write("""
        If you cannot see the side menu and the tabs inside, press the arrows ⏩ in the top left corner.
        Navigate through the various tabs to explore the data and discover insights into the evolution of color and art styles in video games.
    """)
    st.write("""##### 🤔What do the tabs mean?""")
    st.markdown("""
    1. **Art Style Popularity:** View the popularitty of specific styles over time.
    2. **Color through Decades:** See how the industry's average palette has shifted.
    3. **Genre Timelines:** Explore how color trends differ across genres.
    4. **Theme Timelines:** Explore how color trends differ across themes.
    3. **Game Developer Profile:** Explore game studio's most common art styles and colors.
    4. **Individual Game Palette:** Deep-dive into a specific game and look at its screenshots.
    """)

elif page == "Art Style Popularity":
    st.header("📈 Art Style Popularity through Time")
    st.write("""
        This graph shows the division of art styles over time. 
        It shows how many percent of the successfully classified games each style represents in a given year.
        Another graph showing the classification success rate is shown below.
        """)
    classified_df = df[df["is_classified"]]
    style_counts = classified_df.groupby(["Year", "Art_Style"]).size().reset_index(name="Count")
    year_totals = classified_df.groupby("Year").size().reset_index(name="Total")
    perc_df = style_counts.merge(year_totals, on="Year")
    perc_df["Percentage"] = (perc_df["Count"] / perc_df["Total"]) * 100

    fig = px.bar(
        perc_df,
        x="Year",
        y="Percentage",
        color="Art_Style",
        height=600,
        category_orders={"Art_Style": custom_style_order},
        barmode="stack",
    )
    fig.update_yaxes(range=[0, 100])
    fig.update_xaxes(type="linear", range=[1950, 2026])
    fig.update_layout(
        yaxis=dict(
            title_font=dict(size=22),
            tickfont=dict(size=20),
        ),
        xaxis=dict(
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
        font=dict(size=20),
    )
    st.plotly_chart(fig, width="stretch")
    st.info(
        """ 💡TOOL TIP: Hover over the graph to see exact percentages for each style in a given year. 
        You can zoom in and out, and pan over the graph using the icons above the legend.
        You can select which styles to show by clicking on the legend items. Use autoscale to reset the zoom sfter picking the styles."""
    )

    st.divider()

    st.subheader("📈 Dataset Classification Success")
    all_games_decade = df.groupby("Decade")["Unique_ID"].nunique().reset_index(name="Total_Games")
    classified_decade = (
        classified_df.groupby("Decade")["Unique_ID"].nunique().reset_index(name="Classified_Games")
    )
    progress_df = pd.merge(all_games_decade, classified_decade, on="Decade", how="left").fillna(0)
    progress_df["Successful"] = (progress_df["Classified_Games"] / progress_df["Total_Games"]) * 100

    fig = px.bar(
        progress_df,
        x="Decade",
        y="Successful",
        color_discrete_sequence=["#006eff"],
        labels={"Successful": "Success Rate (%)", "Decade": "Decade"},
        text_auto=".1f",
    )
    fig.update_layout(
        yaxis=dict(
            range=[0, 100],
            title_font=dict(size=26),  # Y-axis title
            tickfont=dict(size=22),  # Y-axis numbers (0, 20, 40...)
        ),
        xaxis=dict(
            title_font=dict(size=26),
            tickfont=dict(size=22),
        ),
        font=dict(size=20),
    )
    fig.update_traces(textfont_size=20, textposition="outside", cliponaxis=False)

    st.plotly_chart(fig, width="stretch")

    total_games = df["Unique_ID"].nunique()
    classified_total = classified_df["Unique_ID"].nunique()
    percent_complete = (classified_total / total_games) * 100

    st.caption(
        f"I have successfully classified **{classified_total} out of {total_games}** games (**{percent_complete:.1f}%**)."
    )

    st.divider()
    # st.subheader("🔍 Style Explorer: Random Gallery")
    # st.write("Select an art style to explore random examples from the classified dataset.")

    # # 1. Setup Selection and Button
    # # Get the list of unique art styles present in your classified data
    # available_styles = classified_df["Art_Style"].unique().tolist()

    # col_sel, col_btn = st.columns([3, 1])
    # with col_sel:
    #     selected_style = st.selectbox("Choose a style to explore:", available_styles)
    # with col_btn:
    #     st.write(" ")  # Padding
    #     refresh_button = st.button("🔄 Show Different Games")

    # # 2. Filter the dataset for the selected style
    # style_pool = classified_df[classified_df["Art_Style"] == selected_style]

    # if not style_pool.empty:
    #     # Pick 3 random games from this style
    #     # .sample() handles the randomness
    #     n_samples = min(len(style_pool), 3)
    #     random_games = style_pool.sample(n_samples)

    #     # 3. Display the Gallery
    #     for idx, game_row in random_games.iterrows():
    #         game_name = str(game_row["Game"]).title()
    #         studio_name = str(game_row.get("Developer", "Unknown Studio")).title()
    #         year = int(game_row["Year"])

    #         st.markdown(f"#### 🎮 {game_name} ({year})")
    #         st.markdown(f"**Studio:** {studio_name}")

    #         # Logic: Finding multiple screenshots for the SAME game ID
    #         game_screenshots = df[df["Unique_ID"] == game_row["Unique_ID"]].head(3)

    #         img_cols = st.columns(3)
    #         for i, shot in enumerate(game_screenshots.itertuples()):
    #             with img_cols[i]:
    #                 st.image(shot.Screenshot, width="stretch")
    # else:
    #     st.warning("No games found for this specific style in the current filter.")


elif page == "Color through Decades":
    st.header("🎨 Color through Decades")
    st.subheader("Dominant colors of each decade")

    for dec_label in decades:
        decade_data = df[df["Decade"] == dec_label]

        if not decade_data.empty:
            palette = helper.get_ranked_colors(decade_data, count=10)
            game_count = len(decade_data)

            c1, c2 = st.columns([1, 7])
            formatted_count = f"{game_count:,}".replace(",", " ")

            c1.write(f"### {dec_label}s\n({formatted_count} games)")

            with c2:
                html = '<div style="display: flex; height: 40px; border-radius: 8px; overflow: hidden; border: 3px solid #999; margin-bottom: 2px;">'
                hex_labels = '<div style="display: flex; margin-bottom: 2px;">'

                for c in palette:
                    hex_code = "#%02x%02x%02x" % (int(c.R), int(c.G), int(c.B))
                    rgb_val = f"rgb({int(c.R)},{int(c.G)},{int(c.B)})"
                    html += f'<div style="background-color:{rgb_val}; flex:1;" title="{hex_code.upper()}"></div>'
                    hex_labels += f'<div style="flex:1; text-align:center; font-size:14px; color:gray; font-family:monospace;">{hex_code.upper()}</div>'
                html += "</div>"
                st.markdown(html + hex_labels, unsafe_allow_html=True)

    st.divider()

    st.subheader("Dominant colors in a decade by art style")
    col_decade, col_style = st.columns(2)
    with col_decade:
        decade_sel = st.select_slider(
            "Select Decade", options=[1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
        )
    with col_style:
        df_decade = df[(df["Year"] >= decade_sel) & (df["Year"] < decade_sel + 10)]
        available_styles = sorted(df_decade["Art_Style"].unique().tolist())
        style_choice = st.selectbox("Art Styles", ["All Styles"] + available_styles)

    style_df = df_decade.copy()
    if style_choice != "All Styles":
        style_df = df_decade[df_decade["Art_Style"] == style_choice]

    if not style_df.empty:
        palette = helper.get_representative_palette(style_df, count=10)
        p_cols = st.columns(10)
        for i, color in enumerate(palette):
            p_cols[i].markdown(
                f"<div style='background-color:{color}; height:60px; border-radius:5px; border: 3px solid #999;'></div>",
                unsafe_allow_html=True,
            )
            p_cols[i].caption(color)

        st.subheader(f"Randomized examples from {style_choice} in the {decade_sel}s")
        st.write("Games may be categorized incorrectly, due to the use of user generated keywords")
        style_df_safe = style_df[~style_df["is_nsfw"]]
        if not style_df_safe.empty:
            samples = style_df_safe.sample(min(4, len(style_df_safe)))
            scols = st.columns(4)
            for i, row in enumerate(samples.itertuples()):
                with scols[i % 4]:
                    st.image(row.Screenshot, width="stretch")
                    st.markdown(
                        f"<div style='font-size:14px; text-align:center; color:gray; line-height:1.2; margin-top:5px;'>"
                        f"<b>{row.Game.title()}</b><br>({row.Year})"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info(
                "🎨 Data is being used for palette calculation, but no 'Safe for Work' screenshots are available to display for this selection."
            )


elif page == "Genre Timelines":
    st.header("🎨 Genre-Specific Color Evolution")
    st.info("**💡TOOL TIP**: Click the 🔍 tab to expand and see year-by-year breakdowns")
    st.info("💡Hover mouse over the colors in the breakdown to see their hex codes")
    all_genres = sorted(list(set(df["Genres"].str.split("|").explode().str.strip().unique())))
    selected_genre = st.selectbox(
        "Select Genre", [g for g in all_genres if g], key="genre_trace_box"
    )

    if selected_genre:
        genre_df = df[df["Genre_Set"].apply(lambda x: selected_genre.lower() in x)]

        for dec in decades:
            decade_data_g = genre_df[(genre_df["Year"] >= dec) & (genre_df["Year"] < dec + 10)]
            if not decade_data_g.empty:
                valid_styles = decade_data_g[~decade_data_g["Art_Style"].isin(unclassified_labels)][
                    "Art_Style"
                ]
                top_style = valid_styles.mode()[0] if not valid_styles.empty else "Unknown"

                palette = helper.get_ranked_colors(decade_data_g, count=10)
                st.markdown(
                    f"""
                    <div style='line-height: 1.5;'>
                        <span style='font-size: 25px; font-weight: bold;'>{dec}s </span>
                        <span style='font-size: 18px; color: white;'>Most common art style: {top_style}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                html = '<div style="display: flex; height: 35px; border-radius: 8px; overflow: hidden; border: 3px solid #999; margin-bottom: 3px;">'
                hex_labels = '<div style="display: flex; margin-bottom: 3px;">'

                for col in palette:
                    hex_code = "#%02x%02x%02x" % (int(col.R), int(col.G), int(col.B))
                    rgb_val = f"rgb({int(col.R)},{int(col.G)},{int(col.B)})"
                    html += f'<div style="background-color:{rgb_val}; flex:1;" title="{hex_code.upper()}"></div>'
                    hex_labels += f'<div style="flex:1; text-align:center; font-size:14px; color:gray; font-family:monospace;">{hex_code.upper()}</div>'

                html += "</div>"
                hex_labels += "</div>"
                st.markdown(html + hex_labels, unsafe_allow_html=True)

                # Expandable Year Detail
                with st.expander(f"🔍 View breakdown for the {dec}s"):
                    year_list = sorted(decade_data_g["Year"].unique())  # , reverse=True)
                    for year in year_list:
                        year_data = decade_data_g[decade_data_g["Year"] == year]
                        year_palette = helper.get_ranked_colors(year_data, count=10)

                        col_label, col_strip = st.columns([1, 7])
                        year_count = len(year_data)
                        formatted_year_count = f"{year_count:,}".replace(",", " ")
                        col_label.write(f"**{year}** ({formatted_year_count} games)")
                        with col_strip:
                            y_html = '<div style="display: flex; height: 30px; border-radius: 4px; overflow: hidden; border: 3px solid #666; margin-bottom: 5px;">'
                            for col in year_palette:
                                y_hex = "#%02x%02x%02x" % (
                                    int(col.R),
                                    int(col.G),
                                    int(col.B),
                                )
                                y_html += f'<div style="background-color:{y_hex}; flex:1;" title="{y_hex.upper()}"></div>'
                            y_html += "</div>"
                            st.markdown(y_html, unsafe_allow_html=True)
    st.info(
        """ ☝NOTE: If no games were classified for a specific genre in a decade, the art style will be marked as "Unknown"."""
    )

elif page == "Theme Timelines":
    st.header("🎨 Theme-Specific Color Evolution")
    st.info("**💡TOOL TIP**: Click the 🔍 tab to expand and see year-by-year breakdowns")
    st.info("💡 Hover mouse over the colors in the breakdown to see their hex codes")

    all_themes = sorted(list(set(df["Themes"].str.split("|").explode().str.strip().unique())))
    selected_theme = st.selectbox(
        "Select Theme", [t for t in all_themes if t], key="theme_trace_box"
    )

    if selected_theme:
        theme_df = df[df["Theme_Set"].apply(lambda x: selected_theme.lower() in x)]

        for dec in decades:
            decade_data_t = theme_df[(theme_df["Year"] >= dec) & (theme_df["Year"] < dec + 10)]
            if not decade_data_t.empty:
                valid_styles = decade_data_t[~decade_data_t["Art_Style"].isin(unclassified_labels)][
                    "Art_Style"
                ]
                top_style = valid_styles.mode()[0] if not valid_styles.empty else "Unknown"
                palette = helper.get_ranked_colors(decade_data_t, count=10)

                st.markdown(
                    f"""
                    <div style='line-height: 1.5;'>
                        <span style='font-size: 25px; font-weight: bold;'>{dec}s </span><span style='font-size: 18px; color: white;'>Most common art style: {top_style}</span>
                        
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                html = '<div style="display: flex; height: 35px; border-radius: 8px; overflow: hidden; border: 3px solid #999; margin-bottom: 3px;">'
                hex_labels = '<div style="display: flex; margin-bottom: 3px;">'

                for col in palette:
                    hex_code = "#%02x%02x%02x" % (int(col.R), int(col.G), int(col.B))
                    rgb_val = f"rgb({int(col.R)},{int(col.G)},{int(col.B)})"
                    html += f'<div style="background-color:{rgb_val}; flex:1;" title="{hex_code.upper()}"></div>'
                    hex_labels += f'<div style="flex:1; text-align:center; font-size:14px; color:gray; font-family:monospace;">{hex_code.upper()}</div>'

                html += "</div>"
                hex_labels += "</div>"
                st.markdown(html + hex_labels, unsafe_allow_html=True)

                with st.expander(f"🔍 Detail: {selected_theme.title()} in the {dec}s"):
                    year_list = sorted(decade_data_t["Year"].unique())
                    for year in year_list:
                        year_data = decade_data_t[decade_data_t["Year"] == year]
                        year_palette = helper.get_ranked_colors(year_data, count=10)

                        col_label, col_strip = st.columns([1, 7])
                        year_count = len(year_data)
                        formatted_year_count = f"{year_count:,}".replace(",", " ")
                        col_label.write(f"**{year}** ({formatted_year_count} games)")

                        with col_strip:
                            y_html = '<div style="display: flex; height: 30px; border-radius: 4px; overflow: hidden; border: 3px solid #666; margin-bottom: 5px;">'
                            for col in year_palette:
                                y_hex = "#%02x%02x%02x" % (
                                    int(col.R),
                                    int(col.G),
                                    int(col.B),
                                )
                                y_html += f'<div style="background-color:{y_hex}; flex:1;" title="{y_hex.upper()}"></div>'
                            y_html += "</div>"
                            st.markdown(y_html, unsafe_allow_html=True)
    st.info(
        """ ☝NOTE: If no games were classified for a specific theme in a decade, the art style will be marked as "Unknown"."""
    )

elif page == "Game Developer Profile":
    st.header("🏢 Studios' Color and Style Trends")
    st.subheader("🎮Game Studio All-Time Analysis")
    st.write(
        "Select a major studio from the dropdown or search by name to see their most used colors and art styles"
    )
    col1, col2 = st.columns([1, 2])
    with col1:
        sel_all = st.selectbox(
            "Major Studios (Top 50)",
            ["Select..."] + top_50_global,
            key="all_time_box",
            on_change=helper.on_selectbox_change,
        )
        search_all = st.text_input(
            "Or search by name:",
            "",
            key="all_search",
            on_change=helper.on_text_change,
            help="Searches all developer entries",
        )

        final_all = (
            sel_all
            if sel_all != "Select..."
            else (search_all if search_all.strip() != "" else None)
        )

    if final_all:
        all_df = df[df["Dev_Set"].apply(lambda x: final_all.lower() in x)]
        if all_df.empty:
            with col2:
                st.error(f"❌ Studio '{final_all}' not found. Please check the spelling.")
        else:
            with col2:
                st.write(f"### Palette Signature: {final_all.title()}")
                st.caption(f"{len(all_df)} games analyzed")
                palette_studio = helper.get_representative_palette(all_df, count=10)

                html_bar = '<div style="display: flex; height: 50px; border-radius: 8px; overflow: hidden; border: 3px solid #999; margin-bottom: 2px;">'
                hex_labels = '<div style="display: flex; margin-bottom: 20px;">'
                for color in palette_studio:
                    html_bar += (
                        f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
                    )
                    hex_labels += f'<div style="flex:1; text-align:center; font-size:14px; color:gray; font-family:monospace;">{color.upper()}</div>'
                html_bar += "</div>"
                hex_labels += "</div>"
                st.markdown(html_bar + hex_labels, unsafe_allow_html=True)

                classified_all = all_df[all_df["is_classified"]]
                if not classified_all.empty:
                    fig_all = px.pie(
                        classified_all,
                        names="Art_Style",
                        hole=0.4,
                        height=450,
                        title="Style Distribution",
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        category_orders={"Art_Style": custom_style_order},
                    )
                    fig_all.update_layout(
                        showlegend=True,
                        legend=dict(
                            font=dict(size=20),
                        ),
                    )
                    st.plotly_chart(fig_all, width="stretch")

                    unclassified = ((len(all_df) - len(classified_all)) / len(all_df)) * 100
                    st.caption(f"**{unclassified:.1f}%** of portfolio is unclassified.")
                else:
                    st.warning(f"No games by {final_all.title()} were classified.")
                st.info(
                    "💡TOOL TIP: Hover mouse over the pie chart slices to see the art style names and percentages"
                )

    st.divider()

    st.subheader("📆 Decade-Specific Leaders")
    # dec_sel_s = st.selectbox("Pick Decade", [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020])
    dec_sel_s = st.select_slider(
        "Select Comparison Decade", options=[1970, 1980, 1990, 2000, 2010, 2020], key="dec_slider"
    )

    decade_df = df[(df["Year"] >= dec_sel_s) & (df["Year"] < dec_sel_s + 10)]

    exploded_dec = decade_df["Developers"].str.split("|").explode().str.strip()
    top_10_dec = exploded_dec[exploded_dec != "unknown"].value_counts().nlargest(10).index.tolist()

    col3, col4 = st.columns([1, 2])
    with col3:
        sel_dec = st.selectbox(
            f"Top 10 Studios of the {dec_sel_s}s",
            ["Select..."] + top_10_dec,
            key="dec_box",
            on_change=helper.on_selectbox_change_dec,
        )
        search_dec = st.text_input(
            "Or search by name:", "", key="dec_search", on_change=helper.on_text_change_dec
        )
        final_dec = (
            sel_dec
            if sel_dec != "Select..."
            else (search_dec if search_dec.strip() != "" else None)
        )

    if final_dec:
        dev_df = decade_df[decade_df["Dev_Set"].apply(lambda x: final_dec.lower() in x)]
        if dev_df.empty:
            with col4:
                st.error(
                    f"❌ Studio '{final_dec}' not found in the {dec_sel_s}s. Please check the spelling."
                )
        else:
            with col4:
                st.write(f"### {final_dec.title()}'s Style in the {dec_sel_s}s")
                st.caption(f"{len(dev_df)} games analyzed")
                palette_dec_dev = helper.get_representative_palette(dev_df, count=10)

                html_bar_dec = '<div style="display: flex; height: 40px; border-radius: 8px; overflow: hidden; border: 3px solid #999; margin-bottom: 2px;">'
                hex_labels = '<div style="display: flex; margin-bottom: 20px;">'
                for color in palette_dec_dev:
                    html_bar_dec += (
                        f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
                    )
                    hex_labels += f'<div style="flex:1; text-align:center; font-size:14px; color:gray; font-family:monospace;">{color.upper()}</div>'
                html_bar_dec += "</div>"
                hex_labels += "</div>"
                st.markdown(html_bar_dec + hex_labels, unsafe_allow_html=True)

                classified_dec = dev_df[dev_df["is_classified"]]
                if not classified_dec.empty:
                    style_counts = (
                        classified_dec.groupby("Art_Style").size().reset_index(name="Count")
                    )
                    fig_pie = px.pie(
                        style_counts,
                        values="Count",
                        names="Art_Style",
                        hole=0.4,
                        height=450,
                        title="Technique Distribution",
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        category_orders={"Art_Style": custom_style_order},
                    )
                    fig_pie.update_layout(
                        showlegend=True,
                        legend=dict(
                            font=dict(size=20),
                        ),
                    )
                    st.plotly_chart(fig_pie, width="stretch")
                    unclassified = ((len(dev_df) - len(classified_dec)) / len(dev_df)) * 100
                    if unclassified > 0:
                        st.caption(
                            f"{unclassified:.1f}% of {final_dec.title()}'s {dec_sel_s}s portfolio is unclassified."
                        )
                    else:
                        st.caption(
                            f"All {final_dec.title()}'s games for this period are classified."
                        )
                else:
                    st.warning(f"No games by {final_dec.title()} were classified for this period.")
                st.info(
                    "💡TOOL TIP: Hover mouse over the pie chart slices to see the art style names and percentages"
                )
    st.divider()

    st.subheader("⚔️ Studio Head-to-Head Comparison")
    st.write("Directly compare the artistic evolution of two studios within the same decade.")
    st.info(
        "💡TOOL TIP: You can write in the selectbox fields to quickly find studios by name instead of scrolling through the list."
    )

    decade_comparison = st.select_slider(
        "Select Comparison Decade", options=[1970, 1980, 1990, 2000, 2010, 2020], key="comp_slider"
    )
    compare_df = df[(df["Year"] >= decade_comparison) & (df["Year"] < decade_comparison + 10)]

    all_devs = compare_df["Developers"].str.split("|").explode().str.strip()
    active_devs = sorted(
        [d for d in all_devs.unique().tolist() if d and str(d).lower() != "unknown"]
    )

    col_a, col_b = st.columns(2)
    with col_a:
        studio_a = st.selectbox("Studio A", active_devs, index=0)
    with col_b:
        studio_b = st.selectbox("Studio B", active_devs, index=min(1, len(active_devs) - 1))

    if studio_a and studio_b:
        res_a, res_b = st.columns(2)
        for studio_name, col in [(studio_a, res_a), (studio_b, res_b)]:
            # Filter using the pooled regex logic
            s_df = compare_df[compare_df["Dev_Set"].apply(lambda x: studio_name.lower() in x)]

            with col:
                st.write(f"#### {studio_name.title()}")
                st.caption(f"{len(s_df)} games analyzed")
                pal = helper.get_representative_palette(s_df, count=8)

                html_comp = '<div style="display: flex; height: 35px; border-radius: 6px; overflow: hidden; border: 3px solid #999; margin-bottom: 2px;">'
                hex_labels = '<div style="display: flex; margin-bottom: 20px;">'
                for color in pal:
                    html_comp += f'<div style="background-color:{color}; flex:1;"></div>'
                    hex_labels += f'<div style="flex:1; text-align:center; font-size:14px; color:gray; font-family:monospace;">{color.upper()}</div>'
                html_comp += "</div>"
                hex_labels += "</div>"
                st.markdown(html_comp + hex_labels, unsafe_allow_html=True)

                s_df_classified = s_df[s_df["is_classified"]]
                if not s_df_classified.empty:
                    style_data = s_df_classified["Art_Style"].value_counts().reset_index()
                    style_data.columns = ["Art_Style", "Count"]
                    fig_comp = px.pie(
                        style_data,
                        names="Art_Style",
                        values="Count",
                        hole=0.5,
                        height=375,
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        category_orders={"Art_Style": custom_style_order},
                    )
                    fig_comp.update_layout(showlegend=True, legend=dict(font=dict(size=18)))
                    st.plotly_chart(fig_comp, width="stretch")

                    uncl_comp_pct = ((len(s_df) - len(s_df_classified)) / len(s_df)) * 100
                    st.caption(f"Unclassified: **{uncl_comp_pct:.1f}%**")
                else:
                    st.info("No games were classified")
        st.info(
            "💡TOOL TIP: Hover mouse over the pie chart slices to see the art style names and percentages"
        )

elif page == "Individual Game Palette":
    st.header("🔍 Individual Game Analysis")

    unique_games = sorted(df_safe["Unique_ID"].unique())

    if "search_query" in st.session_state:
        st.session_state["game_selector"] = st.session_state["search_query"]
        del st.session_state["search_query"]

    search_query = st.text_input("Search by name:", "mario")
    if search_query:
        filtered_list = [g for g in unique_games if search_query.lower() in g.lower()]
        filtered_list = [
            g for g in unique_games if search_query.lower() in g.split("[")[0].strip().lower()
        ]
        if not filtered_list:
            st.warning(f"🔍 No games found matching '**{search_query}**'.")
            st.info(
                "💡TOOL TIP: Check for typos or try a broader term (e.g., 'Zelda' instead of 'The Legend of Zelda: Breath of the Wild')."
            )
            st.stop()
    else:
        filtered_list = unique_games

    selected_game_id = st.selectbox("Select a game:", filtered_list, key="game_selector")

    if selected_game_id:
        is_nsfw_check = df[df["Unique_ID"] == selected_game_id]["is_nsfw"].any()

        if is_nsfw_check:
            st.error("⚠️ Content Restricted")
            st.warning(
                "⚠️ This title has been filtered from visual display due to inappropriate content."
            )
            st.stop()

        selected_meta = df_safe[df_safe["Unique_ID"] == selected_game_id].iloc[0]
        target_year = selected_meta["Year"]
        game_rows = df[(df["Unique_ID"] == selected_game_id) & (df["Year"] == target_year)]

        main_info = game_rows.iloc[0]

        st.divider()

        col1, col2 = st.columns([1.5, 2])

        with col1:
            st.title(main_info["Game"].title())
            st.markdown(f"**📅 Year:** {main_info['Year']}")
            st.markdown(f"**🏢 Studio:** {main_info['Developers'].replace('|', ', ').title()}")
            st.markdown(f"**🎨 Art Style:** {main_info['Art_Style']}")
            st.markdown(f"**🕹️ Genres:** {main_info['Genres'].replace('|', ', ').title()}")
            st.markdown(f"**🎭 Themes:** {main_info['Themes'].replace('|', ', ').title()}")
            st.markdown(f"**🖼️ Screenshots:** {len(game_rows)} images")

        with col2:
            st.subheader("🎨 Representative Palette")

            color_profile_str = main_info["Color_profile"]

            html_color_strip = '<div style="display: flex; height: 100px; border-radius: 12px; overflow: hidden;border: 3px solid #999; ">'
            for entry in color_profile_str.split("|"):
                color, weight = entry.split(",")
                html_color_strip += f'''
                    <div title="{color.upper()}" 
                        style="background-color:{color}; flex:{weight}; "cursor: pointer;">
                    </div>'''
            html_color_strip += "</div>"
            st.markdown(html_color_strip, unsafe_allow_html=True)
            st.markdown("Proportionally weighted palette for this game")

            decade_avg_sat = df[df["Decade"] == main_info["Decade"]]["saturation"].mean()
            denom = decade_avg_sat if decade_avg_sat > 0 else 1.0
            factor = main_info["saturation"] / denom

            if factor > 1.5:
                comparison_text = "**exceptionally more vibrant compared to**"
            elif factor > 1.1:
                comparison_text = f"**{factor:.1f}x more colorful compared to**"
            elif factor < 0.5:
                comparison_text = "**highly desaturated compared to**"
            elif factor < 0.9:
                comparison_text = f"**{1 / factor:.1f}x more muted compared to**"
            else:
                comparison_text = "visually consistent with"

            st.write(
                f"{main_info['Game'].title()} is {comparison_text} "
                f" the average game from the {main_info['Decade']}."
            )
            st.info("💡TOOL TIP: Hover over the colors to see their hex codes")

        st.divider()
    st.subheader("🖼️ Source Screenshots")

    n_screens = len(game_rows)
    cols = st.columns(min(n_screens, 5))

    for i, row in enumerate(game_rows.itertuples()):
        with cols[i % 5]:
            st.image(row.Screenshot, width="stretch")
            top_5 = helper.get_ranked_colors(row, count=5)

            mini_html = (
                '<div style="display: flex; height: 25px; '
                'border-radius: 6px; overflow: hidden; border: 3px solid #999; margin-bottom: 25px; margin-top: -5px;">'
            )

            for c in top_5:
                hex_code = f"#{int(c.R):02x}{int(c.G):02x}{int(c.B):02x}".upper()
                mini_html += (
                    f'<div title="{hex_code}" '
                    f'style="background-color:{hex_code}; '
                    f'flex:1; cursor: pointer;"></div>'
                )
            # Padding for games with < 5 colors
            for _ in range(5 - len(top_5)):
                mini_html += '<div style="background-color:#000; flex:1;"></div>'

            mini_html += "</div>"
            st.markdown(mini_html, unsafe_allow_html=True)
    st.info("💡TOOL TIP: Hover over the colors to see their hex codes")

# elif page == "Style Categorizer":
#     st.header("🏷️ Chronological Style Categorizer")

#     # --- 1. File Paths & Initialization ---
#     data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
#     manual_file = os.path.join(data_dir, "manual_classification.csv")
#     valid_ids_file = os.path.join(data_dir, "validated_log.txt")

#     if not os.path.exists(manual_file):
#         pd.DataFrame(columns=["Unique_ID", "Manual_Art_Style"]).to_csv(manual_file, index=False)

#     if not os.path.exists(valid_ids_file):
#         with open(valid_ids_file, "w", encoding="utf-8") as f:
#             f.write("unique_id\n")

#     # --- 2. Load Progress ---
#     manual_df = pd.read_csv(manual_file)
#     with open(valid_ids_file, "r", encoding="utf-8") as f:
#         confirmed_ids = set(line.strip().lower() for line in f.readlines()[1:] if line.strip())

#     csv_ids = set(manual_df["Unique_ID"].astype(str).str.lower().str.strip().unique())
#     done_ids = csv_ids.union(confirmed_ids)

#     # --- 3. Filter Data ---
#     unique_games_df = df_safe.drop_duplicates(subset=["Unique_ID"]).copy()
#     available_data = unique_games_df[
#         ~unique_games_df["Unique_ID"].str.lower().str.strip().isin(done_ids)
#     ].copy()

#     if available_data.empty:
#         st.balloons()
#         st.success("🎉 All games have been categorized!")
#         st.stop()

#     # --- 4. 3-Game Year Cycling Logic ---
#     if "target_year" not in st.session_state:
#         st.session_state.target_year = int(available_data["Year"].min())

#     if "year_counter" not in st.session_state:
#         st.session_state.year_counter = 0

#     # If we've done 3 games or this year is empty, jump to the next year
#     year_pool = available_data[available_data["Year"] == st.session_state.target_year]

#     if st.session_state.year_counter >= 3 or year_pool.empty:
#         remaining_years = available_data[available_data["Year"] > st.session_state.target_year]
#         if remaining_years.empty:
#             st.session_state.target_year = int(available_data["Year"].min())
#         else:
#             st.session_state.target_year = int(remaining_years["Year"].min())

#         st.session_state.year_counter = 0  # Reset counter for the new year
#         if "active_id" in st.session_state:
#             del st.session_state.active_id
#         st.rerun()

#     # Lock in the active game
#     if (
#         "active_id" not in st.session_state
#         or st.session_state.active_id.lower().strip() in done_ids
#     ):
#         st.session_state.active_id = year_pool.iloc[0]["Unique_ID"]

#     # Load UI data
#     game_rows = df[df["Unique_ID"] == st.session_state.active_id]
#     current_game = game_rows.iloc[0]
#     auto_style = str(current_game["Art_Style"])

#     # --- 5. UI ---
#     col_info, col_stats = st.columns([3, 1])
#     with col_info:
#         st.markdown(f"### 🎮 {current_game['Game']} ({int(current_game['Year'])})")
#         st.write(f"Year Progress: **{st.session_state.year_counter + 1} / 3**")

#     with col_stats:
#         st.metric("Total Done", len(done_ids))
#         st.metric("Current Year", st.session_state.target_year)

#     img_cols = st.columns(min(len(game_rows), 4))
#     for i, shot in enumerate(game_rows.head(4).itertuples()):
#         with img_cols[i]:
#             st.image(shot.Screenshot, width="stretch")

#     st.divider()

#     # --- 6. Actions ---
#     col_confirm, col_sel, col_save = st.columns([1, 2, 1])

#     with col_confirm:
#         if st.button(f"✅ Yes, {auto_style}", type="primary", width="stretch"):
#             with open(valid_ids_file, "a", encoding="utf-8") as f:
#                 f.write(f"{st.session_state.active_id}\n")
#             st.session_state.year_counter += 1  # Increment counter
#             del st.session_state.active_id
#             st.rerun()

#     with col_sel:
#         try:
#             d_idx = custom_style_order.index(auto_style)
#         except ValueError:
#             d_idx = 0
#         chosen_style = st.selectbox("Correct Style:", custom_style_order, index=d_idx)

#     with col_save:
#         if st.button("💾 Save & Next", width="stretch"):
#             new_row = pd.DataFrame(
#                 {"Unique_ID": [st.session_state.active_id], "Manual_Art_Style": [chosen_style]}
#             )
#             new_row.to_csv(manual_file, mode="a", header=False, index=False)
#             with open(valid_ids_file, "a", encoding="utf-8") as f:
#                 f.write(f"{st.session_state.active_id}\n")

#             st.session_state.year_counter += 1  # Increment counter
#             del st.session_state.active_id
#             st.rerun()

#     if st.button("⏭️ Skip to Next Year"):
#         st.session_state.year_counter = 3  # Force the jump logic
#         st.rerun()

#     # --- SECTION 2: MARIO PRIORITY QUEUE ---
#     st.divider()
#     st.header("🍄 Named Priority Queue")

#     mario_available = unique_games_df[
#         (unique_games_df["Game"].str.contains("zelda", case=False, na=False))
#         & (~unique_games_df["Unique_ID"].str.lower().str.strip().isin(done_ids))
#     ].copy()

#     if mario_available.empty:
#         st.success("🍄 No more games to categorize!")
#     else:
#         if (
#             "mario_active_id" not in st.session_state
#             or st.session_state.mario_active_id.lower().strip() in done_ids
#         ):
#             st.session_state.mario_active_id = mario_available.iloc[0]["Unique_ID"]

#         m_game_rows = df[df["Unique_ID"] == st.session_state.mario_active_id]
#         m_current = m_game_rows.iloc[0]
#         m_auto_style = str(m_current["Art_Style"])

#         st.subheader(f"{m_current['Game']} ({int(m_current['Year'])})")

#         m_img_cols = st.columns(min(len(m_game_rows), 4))
#         for i, shot in enumerate(m_game_rows.head(4).itertuples()):
#             with m_img_cols[i]:
#                 st.image(shot.Screenshot, width="stretch")

#         m_col1, m_col2, m_col3 = st.columns([1, 2, 1])

#         with m_col1:
#             if st.button(f"✅ Confirm: {m_auto_style}", key="m_confirm"):
#                 with open(valid_ids_file, "a", encoding="utf-8") as f:
#                     f.write(f"{st.session_state.mario_active_id}\n")
#                 del st.session_state.mario_active_id
#                 st.rerun()

#         with m_col2:
#             try:
#                 m_d_idx = custom_style_order.index(m_auto_style)
#             except ValueError:
#                 m_d_idx = 0
#             m_chosen_style = st.selectbox(
#                 "Correct Style:", custom_style_order, index=m_d_idx, key="m_select"
#             )
#             st.write(f"{len(mario_available)} games left")

#         with m_col3:
#             if st.button("💾 Save & Next", key="m_save"):
#                 m_new_row = pd.DataFrame(
#                     {
#                         "Unique_ID": [st.session_state.mario_active_id],
#                         "Manual_Art_Style": [m_chosen_style],
#                     }
#                 )
#                 m_new_row.to_csv(manual_file, mode="a", header=False, index=False)
#                 with open(valid_ids_file, "a", encoding="utf-8") as f:
#                     f.write(f"{st.session_state.mario_active_id}\n")

#                 del st.session_state.mario_active_id
#                 st.rerun()
