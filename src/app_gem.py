import os
import streamlit as st
import pandas as pd
import helper_functions as helper
import plotly.express as px

# --- CONFIG & STYLING ---
st.set_page_config(
    layout="wide", page_title="Evolution of Color and Art Styles in Video Game Design"
)

st.markdown(
    """
    <style>
    /* Target the checkbox label text */
    [data-baseweb="checkbox"] [data-testid="stWidgetLabel"] p {
        font-size: 18px !important;
        font-weight: bold;
    }
    /* Make the slider values/steps bigger */
    [data-testid="stTickBarMinMax"], [data-testid="stTickBar"] {
        font-size: 20px !important;
    }
    /* Make the Label (the title above the slider/selectbox) bigger */
    [data-testid="stWidgetLabel"] p {
        font-size: 22px !important;
        font-weight: 600 !important;
        color: ##bec4eb;
    }    
    /* Make the text INSIDE the Selectbox bigger */
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        font-size: 18px !important;
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
all_analytics = get_summary("color_analytics.parquet")
decade_summary = get_summary("summary_decades.parquet")
screen_data = get_summary("screenshot_colors.parquet")


decades_list = sorted(search_metadata["Decade"].unique().tolist())
unclassified_labels = ["Unclassified", "Unclassified 2D", "Unclassified 3D"]
if st.session_state.get("trigger_nav"):
    st.session_state["page_selection"] = "Individual Game Analysis"
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
        "Individual Game Analysis",
        # "Style Categorizer",
    ],
    key="page_selection",
)
if st.sidebar.button("🎲 Random Game"):
    random_game = search_metadata["Unique_ID"].sample(1).iloc[0]
    st.session_state["search_query"] = random_game
    st.session_state["text_search_box"] = ""
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

    for branch, styles in helper.taxonomy_data.items():
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
                    match = all_analytics[
                        all_analytics["Unique_ID"].str.lower() == game_ref["id"].lower()
                    ]
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
            I have manually classified around 800 games to ensure some level of accuracy, however, it is only a fraction (0.01%) of the total dataset.
            Art is subjective and complex, so my opinion may not always be correct.
            Some games can fit into multiple categories, such as *Worse Than Death (2019)*, which could be both **Stylization: Pixel Art** and **Stylization: Illustrative**.""")
    # total games: 966 446
    col1, col2 = st.columns(2)
    with col1:
        st.image(
            search_metadata[
                search_metadata["Unique_ID"] == "worse than death (2019) [benjamin rivers]"
            ].iloc[0]["Screenshot"],
            width="stretch",
        )
    with col2:
        st.image(
            all_analytics[
                all_analytics["Unique_ID"] == "worse than death (2019) [benjamin rivers]"
            ].iloc[4]["Screenshot"],
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

    st.subheader("Style Distribution by Year")
    pop_df = get_summary("summary_style_popularity.parquet")
    fig = px.bar(
        pop_df,
        x="Year",
        y="Percentage",
        color="Art_Style",
        height=600,
        color_discrete_map=helper.STYLE_COLORS,
        category_orders={"Art_Style": helper.STYLE_ORDER},
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
    st.subheader("Individual Style Trends (Line Chart)")
    fig_line = px.line(
        pop_df,
        x="Year",
        y="Percentage",
        color="Art_Style",
        height=500,
        color_discrete_map=helper.STYLE_COLORS,
        category_orders={"Art_Style": helper.STYLE_ORDER},
    )
    fig_line.update_layout(
        yaxis=dict(
            range=[0, 100],
            title="Percentage of games",
            title_font=dict(size=22),
            tickfont=dict(size=20),
        ),
        xaxis=dict(range=[1950, 2026], title_font=dict(size=22), tickfont=dict(size=20)),
        legend=dict(title="Art Styles", font=dict(size=20), title_font=dict(size=24)),
    )
    # Make lines thicker for better visibility in a thesis
    fig_line.update_traces(line=dict(width=5))
    st.plotly_chart(fig_line, width="stretch")

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
        helper.draw_color_strip(combo_data.iloc[0]["Palette"], height=50)

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

    timeline_df = get_summary(f"summary_{mode.lower()}s.parquet")
    items = sorted(timeline_df["Item"].unique())
    sel_item = st.selectbox(f"Select a {mode}", items)

    item_data = timeline_df[timeline_df["Item"] == sel_item].sort_values("Time")
    item_decades = sorted(item_data[item_data["Type"] == "Decade"]["Time"].unique())

    if item_decades:
        for dec in item_decades:
            dec_row = item_data[(item_data["Type"] == "Decade") & (item_data["Time"] == dec)]
            st.markdown(
                f"""
                <div style='line-height: 1.5;'>
                    <span style='font-size: 25px; font-weight: bold;'>{dec}s </span><span style='font-size: 18px; color: white;'>Games: {dec_row.iloc[0]["Time"]}, Most common art style: {dec_row.iloc[0]["Top_Style"]}</span>
                    
                </div>
                """,
                unsafe_allow_html=True,
            )
            representative_palette = dec_row.iloc[0]["Palette"]
            helper.draw_color_strip(representative_palette, height=45)

            with st.expander(f"🔍 See year-by-year breakdown for the {dec}s"):
                year_data = item_data[
                    (item_data["Type"] == "Year")
                    & (item_data["Time"] >= dec)
                    & (item_data["Time"] < dec + 10)
                ].sort_values("Time")

                for _, row in year_data.iterrows():
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        game_count = row["Time"]  # TODO Count
                        formatted_count = f"{game_count:,}".replace(",", " ")
                        st.markdown(
                            f"""
                            <div>
                                <span style='font-size: 18px; font-weight: bold;'>{row["Time"]} </span>
                                <span style='font-size: 16px; color: white;'> Games: {formatted_count}</span>
                                <div><span style='font-size: 16px; color: white;'> {row["Top_Style"]}</span></div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with col2:
                        helper.draw_color_strip(row["Palette"], height=30)

    st.info("💡Hover mouse over the colors in the breakdown to see their hex codes")


elif page == "Game Developer Profile":
    st.header("🏢 Studios' Color and Style Trends")
    st.subheader("🎮Game Studio All-Time Analysis")
    st.write(
        "Select a major studio from the dropdown or search by name to see their most used colors and art styles"
    )
    studio_summary = get_summary("summary_studios.parquet")

    all_time, decade_spec, h_to_h = st.tabs(
        ["Top 50 All-Time", "Decade Specific Analysis", "Head to Head"]
    )

    with all_time:
        top_50_global = sorted(
            studio_summary[(studio_summary["Decade"] == "All-Time") & (studio_summary["Is_Major"])][
                "Studio"
            ].unique()
        )
        frst = top_50_global[0]
        c1, c2 = st.columns([1, 3])
        with c1:
            sel_all = st.selectbox(
                "Major Studios (Top 50 All-Time)",
                ["Select..."] + top_50_global,
                key="all_time_box",
                on_change=helper.on_selectbox_change,
            )
            search_all = st.text_input(
                "Or search ANY studio by name:",
                # value=frst,
                key="all_search",
                on_change=helper.on_text_change,
            )
            final_all = (
                sel_all
                if sel_all != "Select..."
                else (search_all if search_all.strip() != "" else None)
            )
        studio_name = ""
        dev_row = None

        with c2:
            if final_all:
                studio_match = studio_summary[
                    (studio_summary["Studio"].str.lower() == final_all)
                    & (studio_summary["Decade"] == "All-Time")
                ]
                if studio_match.empty:
                    studio_match = studio_summary[
                        (studio_summary["Studio"].str.contains(final_all, case=False))
                        & (studio_summary["Decade"] == "All-Time")
                    ].head(1)
                if not studio_match.empty:
                    dev_row = studio_match.iloc[0]
                    helper.display_studio_stats(dev_row, "all_time")
                else:
                    st.error(f"❌ Studio '{final_all}' not found. Please check the spelling.")
            else:
                st.info("Select a major studio or search by name to begin")
    with decade_spec:
        st.subheader("📆 Decade-Specific Leaders")
        all_years = sorted([y for y in studio_summary["Decade"].unique() if y != "All-Time"])
        sel_dec = st.select_slider("Select Decade", options=all_years)

        if "final_studio_choice" not in st.session_state:
            st.session_state["final_studio_choice"] = None
        current_choice = None
        c1, c2 = st.columns([1, 3])

        with c1:
            major_in_dec = studio_summary[
                (studio_summary["Decade"] == str(sel_dec)) & (studio_summary["Is_Major"])
            ]["Studio"].tolist()
            major_options = ["Select..."] + sorted(major_in_dec)

            sel_studio = st.selectbox(f"Major Studios in {sel_dec}s", major_options, index=0)
            search_dec = st.text_input("Or search ANY studio name:", key="dec_search_input")

            if sel_studio != "Select...":
                st.session_state["final_studio_choice"] = sel_studio
            elif search_dec.strip() != "":
                st.session_state["final_studio_choice"] = search_dec.strip().lower()

        with c2:
            current_choice = st.session_state["final_studio_choice"]

            if not current_choice:
                st.info("Select a major studio or search by name to begin")
            else:
                row = studio_summary[
                    (studio_summary["Studio"] == current_choice)
                    & (studio_summary["Decade"] == str(sel_dec))
                ]

                if not row.empty:
                    helper.display_studio_stats(row.iloc[0], "decade_spec")
                else:
                    st.warning(
                        f"⚠️ **{current_choice.title()}** has no recorded releases in the **{sel_dec}s**."
                    )
                    all_entries = studio_summary[studio_summary["Studio"] == current_choice]

                    if not all_entries.empty:
                        active_years = sorted(
                            [d for d in all_entries["Decade"].unique() if d != "All-Time"]
                        )
                        st.info(
                            f"💡 Try moving the slider. {current_choice.title()} is active in: {', '.join(active_years)}"
                        )
                    else:
                        st.error(f"❌ Studio '{current_choice}' not found in the master database.")

        # if st.button("Clear Selection"):
        #     st.session_state["final_studio_choice"] = None
        #     st.rerun()
    with h_to_h:
        st.subheader("⚔️ Studio Head-to-Head Comparison")
        st.write("Directly compare the artistic evolution of two studios within the same decade.")
        st.info(
            "💡TOOL TIP: You can write in the selectbox fields to quickly find studios by name instead of scrolling through the list. If you need ideas what studios to compare in each decade, check the *Decade Specific Analysis* section"
        )
        c1, c2 = st.columns([1, 6])
        with c1:
            use_all_time = st.checkbox("View All-Time Data", value=False, key="h2h_all_time")
        with c2:
            selected_decade = st.select_slider(
                "Select Decade for Comparison",
                options=all_years,
                disabled=use_all_time,
                label_visibility="collapsed" if use_all_time else "visible",
                key="h2h_slider",
            )
        search_decade = "All-Time" if use_all_time else str(selected_decade)
        all_studios_global = sorted(studio_summary["Studio"].unique())
        if "h2h_a" not in st.session_state:
            st.session_state["h2h_a"] = all_studios_global[0]
        if "h2h_b" not in st.session_state:
            st.session_state["h2h_b"] = all_studios_global[min(1, len(all_studios_global) - 1)]

        col_a, col_b = st.columns(2)
        with col_a:
            options_a = [s for s in all_studios_global if s != st.session_state["h2h_b"]]
            studio_a = st.selectbox(
                "Studio A",
                options_a,
                index=options_a.index(st.session_state["h2h_a"])
                if st.session_state["h2h_a"] in options_a
                else 0,
                key="select_a",
            )
            st.session_state["h2h_a"] = studio_a
            row_a = studio_summary[
                (studio_summary["Studio"] == studio_a) & (studio_summary["Decade"] == search_decade)
            ]
            if not row_a.empty:
                helper.display_studio_stats(row_a.iloc[0], "h_to_h", suffix="h2h_left")
            else:
                st.warning(f"No data for {studio_a} in the {search_decade}s.")
                other_decs = studio_summary[
                    (studio_summary["Studio"] == studio_a)
                    & (studio_summary["Decade"] != "All-Time")
                ]["Decade"].unique()
                if len(other_decs) > 0:
                    st.caption(f"Active in: {', '.join(sorted(other_decs))}")

        with col_b:
            options_b = [s for s in all_studios_global if s != st.session_state["h2h_a"]]
            studio_b = st.selectbox(
                "Studio B",
                options_b,
                index=options_b.index(st.session_state["h2h_b"])
                if st.session_state["h2h_b"] in options_b
                else 0,
                key="select_b",
            )
            st.session_state["h2h_b"] = studio_b
            row_b = studio_summary[
                (studio_summary["Studio"] == studio_b) & (studio_summary["Decade"] == search_decade)
            ]
            if not row_b.empty:
                helper.display_studio_stats(row_b.iloc[0], "h_to_h", suffix="h2h_right")
            else:
                st.warning(f"No data for {studio_b} in the {search_decade}s.")
                other_decs = studio_summary[
                    (studio_summary["Studio"] == studio_b)
                    & (studio_summary["Decade"] != "All-Time")
                ]["Decade"].unique()
                if len(other_decs) > 0:
                    st.caption(f"Active in: {', '.join(sorted(other_decs))}")


elif page == "Individual Game Analysis":
    st.header("🔍 Individual Game Analysis")

    unique_games = sorted(search_metadata["Unique_ID"].unique())

    search_input = st.text_input("Search by name:", key="text_search_box")

    # 2. Filtering
    if search_input:
        filtered_list = [g for g in unique_games if search_input.lower() in g.lower()]
    else:
        filtered_list = unique_games

    # 3. Handle the Random Button override
    # If 'search_query' exists (from the sidebar), we force it to the front of the list
    if "search_query" in st.session_state:
        target_game = st.session_state["search_query"]
        if target_game in unique_games:
            filtered_list = [target_game] + [g for g in filtered_list if g != target_game]
        del st.session_state["search_query"]

    selected_game_id = st.selectbox("Select a game:", filtered_list, index=0)

    if selected_game_id:
        game_rows = all_analytics[all_analytics["Unique_ID"] == selected_game_id]

        if game_rows.empty:
            st.error("Data for this game could not be found.")
            st.stop()

        if game_rows["Is_NSFW"].any():
            st.warning("This game has sexual content")
        #     st.error("⚠️ Content Restricted")
        #     st.warning(
        #         "This title has been filtered from visual display due to inappropriate content."
        #     )
        # st.stop()

        main_info = game_rows.iloc[0]
        col1, col2 = st.columns([1.5, 2])

        with col1:
            st.title(main_info["Game"].title())
            st.markdown(f"**📅 Year:** {main_info['Year']}")
            st.markdown(f"**🏢 Studio:** {main_info['Developers'].replace('|', ', ').title()}")
            st.markdown(f"**🎨 Art Style:** {main_info['Art_Style']}")
            st.markdown(f"**🕹️ Genres:** {main_info['Genres'].replace('|', ', ').title()}")
            st.markdown(f"**🎭 Themes:** {main_info['Themes'].replace('|', ', ').title()}")
            st.markdown(f"**🖼️ Screenshots:** {len(game_rows)} image(s) analyzed")

        with col2:
            st.subheader("🎨 Weighted Representative Palette")
            color_profile_str = main_info["Color_palette"]

            html_color_strip = '<div style="display: flex; height: 100px; border-radius: 8px; overflow: hidden; border: 3px solid #999;">'
            for entry in color_profile_str.split("|"):
                # st.info(entry)
                if "," in entry:
                    color, weight = entry.split(",")
                    html_color_strip += f'''
                        <div title="{color.upper()}" 
                             style="background-color:{color}; flex:{weight};">
                        </div>'''
            html_color_strip += "</div>"

            st.markdown(html_color_strip, unsafe_allow_html=True)
            st.caption("Proportionally weighted palette (DNA) for this specific title.")

            dec_avg_row = decade_summary[
                (decade_summary["Decade"] == main_info["Decade"])
                & (decade_summary["Art_Style"] == "Global")
            ]

            if not dec_avg_row.empty:
                decade_avg_sat = dec_avg_row.iloc[0]["Decade_Avg_Sat"]
                denom = decade_avg_sat if decade_avg_sat > 0 else 1.0
                factor = main_info["saturation"] / denom

                if factor > 1.5:
                    comparison_text = "**exceptionally more vibrant than**"
                elif factor > 1.1:
                    comparison_text = f"**{factor:.1f}x more colorful than**"
                elif factor < 0.5:
                    comparison_text = "**highly desaturated compared to**"
                elif factor < 0.9:
                    comparison_text = f"**{1 / factor:.1f}x more muted than**"
                else:
                    comparison_text = "visually consistent with"

                st.info(
                    f"{main_info['Game'].title()} is {comparison_text} "
                    f"the average game from the {main_info['Decade']}s."
                )

        st.divider()

        st.subheader("🖼️ Source Screenshots & Local Palettes")
        # screen_data = get_summary("screenshot_colors.parquet")

        # cols = st.columns(3)
        # screens = screen_data[screen_data["Unique_ID"] == selected_game_id]
        # for i, row in enumerate(screens.itertuples()):
        #     with cols[i % 3]:
        #         st.image(row.Screenshot, width="stretch")

        #         mini_html = (
        #             '<div style="display: flex; height: 30px; border-radius: 6px; '
        #             'overflow: hidden; border: 2px solid #555; margin-bottom: 30px; margin-top: -5px;">'
        #         )

        #         for j in range(1, 10):
        #             r = getattr(row, f"C{j}_R")
        #             g = getattr(row, f"C{j}_G")
        #             b = getattr(row, f"C{j}_B")
        #             if pd.isna(r) or pd.isna(g) or pd.isna(b):
        #                 continue
        #             hex_code = f"#{int(r):02x}{int(g):02x}{int(b):02x}".upper()

        #             mini_html += (
        #                 f'<div title="{hex_code}" '
        #                 f'style="background-color:{hex_code}; flex:1; cursor: pointer;"></div>'
        #             )

        #         mini_html += "</div>"
        #         st.markdown(mini_html, unsafe_allow_html=True)

        # st.info("💡 TOOL TIP: Hover over any color block to see the specific Hex Code.")

# elif page == "Style Categorizer":
#     st.header("🏷️ Research Validation & Categorizer")

#     # --- 1. File Paths & Initialization ---
#     data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
#     manual_file = os.path.join(data_dir, "manual_classification.csv")
#     valid_ids_file = os.path.join(data_dir, "validated_log.txt")

#     # Ensure files exist
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

#     # Use the master color analytics file for classification work
#     master_df = get_summary("color_analytics.parquet")
#     # Use the screenshot file for the visual gallery
#     screen_df = get_summary("screenshot_colors.parquet")

#     # Filter out games already processed
#     available_data = master_df[
#         ~master_df["Unique_ID"].str.lower().str.strip().isin(done_ids)
#     ].copy()

#     # --- 3. SECTION 1: CHRONOLOGICAL VALIDATION (Top) ---
#     st.subheader("⏳ Chronological Validation")
#     st.caption("Validating games that already have a classified Art Style from the taxonomy.")

#     # Filter for games that ARE classified but NOT validated
#     chrono_pool = available_data[available_data["Is_classified"]].sort_values("Year")

#     if chrono_pool.empty:
#         st.success("🎉 All automatically classified games have been validated!")
#     else:
#         # Lock in current game
#         if "chrono_id" not in st.session_state or st.session_state.chrono_id in done_ids:
#             st.session_state.chrono_id = chrono_pool.iloc[0]["Unique_ID"]

#         current_game = chrono_pool[chrono_pool["Unique_ID"] == st.session_state.chrono_id].iloc[0]
#         game_screens = screen_df[screen_df["Unique_ID"] == st.session_state.chrono_id]

#         c1, c2 = st.columns([3, 1])
#         with c1:
#             st.markdown(f"### {current_game['Game']} ({current_game['Year']})")
#             st.write(
#                 f"Studio: `{current_game['Developers']}` | System Suggestion: **{current_game['Art_Style']}**"
#             )
#         with c2:
#             st.metric("Pending Validation", len(chrono_pool))

#         # Show Screenshots
#         img_cols = st.columns(len(game_screens) if len(game_screens) > 0 else 1)
#         for i, shot in enumerate(game_screens.itertuples()):
#             with img_cols[i % len(img_cols)]:
#                 st.image(shot.Screenshot, width="stretch")

#         v_col1, v_col2, v_col3 = st.columns([1, 2, 1])
#         with v_col1:
#             if st.button(f"✅ Correct: {current_game['Art_Style']}", key="v_auto", type="primary"):
#                 with open(valid_ids_file, "a", encoding="utf-8") as f:
#                     f.write(f"{st.session_state.chrono_id}\n")
#                 st.rerun()

#         with v_col2:
#             # Assumes custom_style_order is defined in your constants
#             new_style = st.selectbox("Actually, it is:", helper.STYLE_ORDER, key="v_select")

#         with v_col3:
#             if st.button("💾 Overwrite & Save", key="v_save"):
#                 new_row = pd.DataFrame(
#                     {"Unique_ID": [st.session_state.chrono_id], "Manual_Art_Style": [new_style]}
#                 )
#                 new_row.to_csv(manual_file, mode="a", header=False, index=False)
#                 with open(valid_ids_file, "a", encoding="utf-8") as f:
#                     f.write(f"{st.session_state.chrono_id}\n")
#                 st.rerun()

#     st.divider()

#     # --- 4. SECTION 2: NAMED PRIORITY QUEUE (Bottom) ---
#     st.subheader("🔍 Search & Categorize Specific Titles")
#     search_term = st.text_input(
#         "Enter game title keywords (e.g., 'mario', 'zelda', 'final fantasy'):", "mario"
#     ).lower()

#     named_available = available_data[
#         available_data["Game"].str.contains(search_term, case=False, na=False)
#     ].sort_values("Year")

#     if named_available.empty:
#         st.info(f"No unclassified games found matching '{search_term}'.")
#     else:
#         if (
#             "search_active_id" not in st.session_state
#             or st.session_state.search_active_id in done_ids
#         ):
#             st.session_state.search_active_id = named_available.iloc[0]["Unique_ID"]

#         s_game = named_available[
#             named_available["Unique_ID"] == st.session_state.search_active_id
#         ].iloc[0]
#         s_screens = screen_df[screen_df["Unique_ID"] == st.session_state.search_active_id]

#         st.markdown(f"#### {s_game['Game']} ({s_game['Year']})")
#         st.caption(f"Currently: {s_game['Art_Style']} | {len(named_available)} results left")

#         s_img_cols = st.columns(len(s_screens) if len(s_screens) > 0 else 1)
#         for i, shot in enumerate(s_screens.itertuples()):
#             with s_img_cols[i % len(s_img_cols)]:
#                 st.image(shot.Screenshot, width="stretch")

#         s_col1, s_col2, s_col3 = st.columns([1, 2, 1])
#         with s_col1:
#             if st.button(f"✅ Keep: {s_game['Art_Style']}", key="s_keep"):
#                 with open(valid_ids_file, "a", encoding="utf-8") as f:
#                     f.write(f"{st.session_state.search_active_id}\n")
#                 st.rerun()

#         with s_col2:
#             s_chosen = st.selectbox("Assign New Style:", helper.STYLE_ORDER, key="s_select")

#         with s_col3:
#             if st.button("💾 Save Manual Entry", key="s_save"):
#                 new_row = pd.DataFrame(
#                     {
#                         "Unique_ID": [st.session_state.search_active_id],
#                         "Manual_Art_Style": [s_chosen],
#                     }
#                 )
#                 new_row.to_csv(manual_file, mode="a", header=False, index=False)
#                 with open(valid_ids_file, "a", encoding="utf-8") as f:
#                     f.write(f"{st.session_state.search_active_id}\n")
#                 st.rerun()
