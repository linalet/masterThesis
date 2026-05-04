import os
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import helper_functions as helper
import plotly.express as px
import pyarrow.parquet as pq

st.set_page_config(
    layout="wide", page_title="Evolution of Color and Art Styles in Video Game Design"
)

st.markdown(
    """
    <style>
    /* Target the checkbox label text */
    [data-baseweb="checkbox"] [data-testid="stWidgetLabel"] p {
        font-size: 18px + 0.5vw !important;
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
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size:25px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")


@st.cache_data
def get_summary(filename):
    return pd.read_parquet(os.path.join(DATA_PATH, filename))


@st.cache_data
def get_game_analytics(game_id: str):
    path = os.path.join(BASE_DIR, "data", "color_analytics.parquet")
    table = pq.read_table(path, filters=[("Unique_ID", "=", game_id)])
    return table.to_pandas()


@st.cache_data
def get_specific_game_screenshots(game_id):
    path = os.path.join(BASE_DIR, "data", "screenshot_colors.parquet")
    table = pq.read_table(path, filters=[("Unique_ID", "=", game_id)])
    return table.to_pandas()


search_metadata = get_summary("search_metadata.parquet")

unclassified_labels = ["Unclassified", "Unclassified 2D", "Unclassified 3D"]
if st.session_state.get("trigger_nav"):
    st.session_state["page_selection"] = "Individual Game Analysis"
    st.session_state["trigger_nav"] = False

with st.sidebar:
    page = option_menu(
        None,
        options=[
            "Project Overview",
            "Art Style Popularity",
            "Color through Decades",
            "Genre Timelines",
            "Theme Timelines",
            "Game Developer Profile",
            "Individual Game Analysis",
        ],
        icons=[
            "info-circle",
            "graph-up",
            "palette",
            "palette",
            "palette",
            "building",
            "search",
        ],
        menu_icon="house",
        default_index=0,
        styles={
            "container": {"padding": "0!important"},
            "icon": {"font-size": "18px+ 0.5vw"},
            "nav-link": {
                "font-size": "16px + 0.5vw",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#7DABCC",
            },
            "nav-link-selected": {"background-color": "#0067B0"},
        },
    )
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
        st.write(
            """
                 I have collected all my data from [IGDB.com](%s), which is currently the largest video game database in the world.
        """
            % url
        )
    with col2:
        st.header("⚙️ Research Questions")
        st.info(
            "* **Q1:** How will the features in the dashboard be used to analyze the collected data?"
        )
        st.info("* **Q2:** Which insights can the users gain from the visualized data?")

    st.divider()

    st.header("🏷️ Art Style Taxonomy & Classification Logic")
    st.write(
        """
            I have developed my own game art style taxonomy for the purposes of this thesis. 
            Games are divided into 3 main categories: **Realism**, **Stylization**, and **Abstraction**.
            They are further divided into sub-categories based on keywords used to describe the game. Read more below for the detailed classification logic and examples.
            """
    )
    all_analytics = get_summary("homepage_samples.parquet")
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
            I have manually classified around 1300 games to ensure some level of accuracy, however, it is only a fraction (0.1%) of the total dataset.
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
    st.write("""##### 🤔What do the pages mean?""")
    st.markdown("""
    1. **Art Style Popularity:** View the popularity of specific styles over time.
    2. **Color through Decades:** See how the industry's average palette has shifted. Look at color palettes for different art styles in a decade.
    3. **Genre Timelines:** Explore how color trends differ across genres.
    4. **Theme Timelines:** Explore how color trends differ across themes.
    3. **Game Developer Profile:** Explore game studio's most common art styles and colors or compare 2 studios.
    4. **Individual Game Palette:** Deep-dive into a specific game and look at its screenshots.
    """)

elif page == "Art Style Popularity":
    st.header("📈 Art Style Popularity through Time")
    st.info("💡TOOL TIP: Switch between the tabs to see other visualizations.")
    graph_tab = option_menu(
        None,
        ["Art style distribution", "Art style popularity", "Classification success"],
        icons=["bar-chart-fill", "graph-up", "bar-chart-fill"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#7DABCC",
            },
            "nav-link-selected": {"background-color": "#0067B0"},
        },
    )
    pop_df = get_summary("summary_style_popularity.parquet")
    if graph_tab == "Art style distribution":
        st.subheader("Style Distribution by Year")
        st.write("""
        This graph shows the division of art styles over time. 
        It shows how many percent of the successfully classified games each style represents in a given year.
        """)
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
                range=[1950, 2027],
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
            """💡TOOL TIP: Hover over the graph to see exact percentages for each style in a given year. 
            You can zoom in and out, and pan over the graph using the icons above the legend.
            You can select which styles to show by clicking on the legend items. Use autoscale to reset the zoom after picking the styles."""
        )
    if graph_tab == "Art style popularity":
        st.subheader("Individual Style Trends")
        st.write("This graph shows the popularity of each style through history.")
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
            xaxis=dict(range=[1950, 2027], title_font=dict(size=22), tickfont=dict(size=20)),
            legend=dict(title="Art Styles", font=dict(size=20), title_font=dict(size=24)),
        )
        # Make lines thicker for better visibility in a thesis
        fig_line.update_traces(line=dict(width=5))
        st.plotly_chart(fig_line, width="stretch")
        st.info(
            """ 💡TOOL TIP: Hover over the graph to see exact percentages for each style in a given year. 
            You can zoom in and out, and pan over the graph using the icons above the legend.
            You can select which styles to show by clicking on the legend items. Use autoscale to reset the zoom after picking the styles."""
        )

    if graph_tab == "Classification success":
        st.subheader("📈% of Games Categorized by Decade")
        st.write(
            "This graph illustrates the percentage of games classified into an art style for each decade."
        )
        success_df = get_summary("summary_success_rate.parquet")
        fig2 = px.bar(
            success_df,
            x="Decade",
            y="Rate",
            text_auto=".1f",
        )
        fig2.update_layout(
            yaxis=dict(
                range=[0, 100],
                title_font=dict(size=26),
                tickfont=dict(size=22),
            ),
            xaxis=dict(
                range=[1945, 2027],
                title_font=dict(size=26),
                tickfont=dict(size=22),
            ),
            font=dict(size=20),
        )
        st.plotly_chart(fig2, width="stretch")
        overall_val = success_df[success_df["Decade"] == 3000]["Rate"].values[0]
        st.info(f"{overall_val:.2f}% of all games were assigned an art style")

elif page == "Color through Decades":
    st.header("🎨 Color through Decades")
    st.subheader("Dominant colors of each decade")

    decades_list = sorted(search_metadata["Decade"].unique().tolist())
    decade_summary = get_summary("summary_decades.parquet")
    tabs = option_menu(
        None,
        ["Decade color palettes", "Palettes per artstyle"],
        icons=["palette", "palette"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#7DABCC",
            },
            "nav-link-selected": {"background-color": "#0067B0"},
        },
    )

    if tabs == "Decade color palettes":
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

    if tabs == "Palettes per artstyle":
        st.subheader("Dominant colors in a decade by art style.")
        decades_list = sorted(search_metadata["Decade"].unique().tolist())

        col_decade, col_style = st.columns([3, 1])
        sel_dec = col_decade.select_slider("Select Decade", options=decades_list)

        available_styles = sorted(
            decade_summary[decade_summary["Decade"] == sel_dec]["Art_Style"].unique().tolist()
        )
        if "Unclassified" in available_styles:
            available_styles.remove("Unclassified")
        if "Global" in available_styles:
            available_styles.remove("Global")

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
            st.write(
                "Games may be categorized incorrectly, due to the use of user generated keywords."
            )
            samples = search_metadata[
                (search_metadata["Decade"] == sel_dec)
                & (search_metadata["Art_Style"] == sel_style)
                & (search_metadata["Is_NSFW"] == False)
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
            st.info("🎨 No screenshots are available to display for this selection.")

elif page in ["Genre Timelines", "Theme Timelines"]:
    mode = "Genre" if "Genre" in page else "Theme"
    st.header(f"🎨 {mode}-Specific Color Evolution")
    st.write(f"Exploration of how the use of colors changed depending on the {mode}.")
    st.info("**💡TOOL TIP**: Click the 🔍 tab to expand and see year-by-year breakdowns.")

    timeline_df = get_summary(f"summary_{mode.lower()}s.parquet")
    items = sorted(timeline_df["Item"].unique())
    sel_item = st.selectbox(f"Select a {mode}", items)

    item_data = timeline_df[timeline_df["Item"] == sel_item].sort_values("Time")
    item_decades = sorted(item_data[item_data["Type"] == "Decade"]["Time"].unique())

    if item_decades:
        for dec in item_decades:
            dec_row = item_data[(item_data["Type"] == "Decade") & (item_data["Time"] == dec)]
            formatted_count = f"{dec_row.iloc[0]['Count']:,}".replace(",", " ")
            st.markdown(
                f"""
                <div style='line-height: 1.5;'>
                    <span style='font-size: 22px; font-weight: bold;'>{dec}s </span><span style='font-size: 18px; color: gray;'>Games: {formatted_count}, Most common art style: {dec_row.iloc[0]["Top_Style"]}</span>
                    
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
                        game_count = row["Count"]
                        formatted_count = f"{game_count:,}".replace(",", " ")
                        st.markdown(
                            f"""
                            <div>
                                <span style='font-size: 18px; font-weight: bold;'>{row["Time"]} </span>
                                <span style='font-size: 16px;'> Games: {formatted_count}</span>
                                <div><span style='font-size: 16px;'> {row["Top_Style"]}</span></div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with col2:
                        helper.draw_color_strip(row["Palette"], height=30)

    st.info(
        f""" ☝NOTE: If no games were classified for a specific {mode.lower()} in a decade, the art style will be marked as "Unknown"."""
    )


elif page == "Game Developer Profile":
    st.header("🏢 Studios' Color and Style Trends")
    st.subheader("🎮Game Studio All-Time Analysis")
    st.write(
        "Select a major studio from the dropdown or search by name to see their most used colors and art styles."
    )
    studio_summary = get_summary("summary_studios.parquet")

    # all_time, decade_spec, h_to_h = st.tabs(
    #     ["|All-Time Analysis", "|Decade Specific Analysis", "|Studio Comparison"]
    # )
    studio_tabs = option_menu(
        None,
        ["All-Time Analysis", "Decade Specific Analysis", "Studio Comparison"],
        # icons=["palette", "palette"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#7DABCC",
            },
            "nav-link-selected": {"background-color": "#0067B0"},
        },
    )
    all_years = sorted([y for y in studio_summary["Decade"].unique() if y != "All-Time"])

    if studio_tabs == "All-Time Analysis":
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
                    helper.display_studio_stats(studio_match.iloc[0], "all_time")
                else:
                    st.error(f"❌ Studio '{final_all}' not found. Please check the spelling.")
            else:
                st.info("Select a major studio or search by name to begin.")
    if studio_tabs == "Decade Specific Analysis":
        st.subheader("📆 Decade-Specific Leaders")
        sel_dec = st.select_slider("Select Decade", options=all_years)

        if "active_studio_id" not in st.session_state:
            st.session_state["active_studio_id"] = None

        c1, c2 = st.columns([1, 3])

        with c1:
            major_in_dec = studio_summary[
                (studio_summary["Decade"] == str(sel_dec)) & (studio_summary["Is_Major"])
            ]["Studio"].tolist()
            major_options = ["Select..."] + sorted(major_in_dec)

            sel_studio = st.selectbox(
                f"Major Studios in {sel_dec}s",
                major_options,
                key="dec_sel_widget",
                on_change=helper.on_selectbox_change_dec,
            )
            search_dec = st.text_input(
                "Or search ANY studio name:",
                key="dec_text_input",
                on_change=helper.on_text_change_dec,
            )

        with c2:
            final_choice = st.session_state["active_studio_id"]
            if not final_choice:
                st.info("Select a major studio or search by name to begin.")
            else:
                row = studio_summary[
                    (studio_summary["Studio"].str.lower() == final_choice)
                    & (studio_summary["Decade"] == str(sel_dec))
                ]
                if row.empty:
                    row = studio_summary[
                        (studio_summary["Studio"].str.contains(final_choice, case=False))
                        & (studio_summary["Decade"] == str(sel_dec))
                    ].head(1)
                if not row.empty:
                    helper.display_studio_stats(row.iloc[0], "decade_spec")
                else:
                    all_entries = studio_summary[
                        studio_summary["Studio"].str.contains(final_choice, case=False)
                    ]

                    if not all_entries.empty:
                        st.warning(
                            f"⚠️ **{all_entries.iloc[0]['Studio'].title()}** has no recorded releases in the **{sel_dec}s**."
                        )
                        active_years = sorted(
                            [d for d in all_entries["Decade"].unique() if d != "All-Time"]
                        )
                        st.info(
                            f"💡 TOOL TIP: Try moving the slider. {all_entries.iloc[0]['Studio'].title()} is active in: {', '.join(active_years)}"
                        )
                    else:
                        st.error(f"❌ Studio '{final_choice}' not found in the master database.")

    if studio_tabs == "Studio Comparison":
        st.subheader("⚔️ Studio Head-to-Head Comparison")
        st.write("Directly compare the artistic evolution of two studios within the same decade.")
        st.info(
            "💡TOOL TIP: You can write in the selectbox fields to quickly find studios by name instead of scrolling through the list. If you need ideas what studios to compare in each decade, check the *Decade Specific Analysis* section."
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
                    st.info(
                        f"💡 TOOL TIP: Try moving the slider. {studio_a.title()} is active in: {', '.join(sorted(other_decs))}"
                    )

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
                    st.info(
                        f"💡 TOOL TIP: Try moving the slider. {studio_b.title()} is active in: {', '.join(sorted(other_decs))}"
                    )


elif page == "Individual Game Analysis":
    st.header("🔍 Individual Game Analysis")

    if st.button("🎲 Random Game"):
        random_game = search_metadata["Unique_ID"].sample(1).iloc[0]
        st.session_state["search_query"] = random_game
        st.session_state["trigger_nav"] = True
        st.rerun()
    st.info(
        """💡TOOL TIP: Start writing a game title, then pick the specific game from the selectbox. E.g., "mario kart" -> "mario kart wii (2008) [nintendo]". """
    )

    decade_summary = get_summary("summary_decades.parquet")

    unique_games = sorted(search_metadata["Unique_ID"].unique())

    search_input = st.text_input("Search by name:", key="text_search_box")

    if search_input:
        search_term = search_input.lower()
        filtered_list = search_metadata[
            search_metadata["Unique_ID"].str.contains(search_term, case=False)
        ]["Unique_ID"].tolist()
    else:
        filtered_list = []

    if "search_query" in st.session_state:
        target_game = st.session_state["search_query"]
        if target_game in unique_games:
            filtered_list = [target_game] + [g for g in filtered_list if g != target_game]
        del st.session_state["search_query"]

    if search_input and not filtered_list:
        st.warning("No game found. Chcek the spelling or try another game")

    selected_game_id = st.selectbox(
        "Select a game:",
        filtered_list if filtered_list else [],
        index=0,
    )

    if selected_game_id:
        game_rows = get_game_analytics(selected_game_id)
        main_info = search_metadata[search_metadata["Unique_ID"] == selected_game_id].iloc[0]

        if game_rows.empty:
            st.error("Data for this game could not be found.")
            st.stop()

        if main_info["Is_NSFW"]:
            st.warning("⚠️This game contains sexual content.")

        color_info = game_rows.iloc[0]
        col1, col2 = st.columns([1.5, 2])

        with col1:
            st.title(main_info["Game"].title())
            st.markdown(f"**📅 Year:** {main_info['Year']}")
            st.markdown(f"**🏢 Studio:** {main_info['Developers'].replace('|', ', ').title()}")
            st.markdown(f"**🎨 Art Style:** {main_info['Art_Style']}")
            st.markdown(f"**🕹️ Genres:** {main_info['Genres'].replace('|', ', ').title()}")
            st.markdown(f"**🎭 Themes:** {main_info['Themes'].replace('|', ', ').title()}")

        with col2:
            st.subheader("🎨 Weighted Representative Palette")
            color_profile_str = color_info["Color_Palette"]

            html_color_strip = '<div style="display: flex; height: 100px; border-radius: 8px; overflow: hidden; border: 3px solid #999;">'
            for entry in color_profile_str.split("|"):
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
                dec_var = dec_avg_row.iloc[0]["Decade_Avg_Var"]
                game_var = color_info["Sat_Variance"]
                var_factor = game_var / dec_var if dec_var > 0 else 1.0

                dec_sat = dec_avg_row.iloc[0]["Decade_Avg_Sat"]
                game_sat = color_info["Saturation"]
                sat_factor = game_sat / dec_sat if dec_sat > 0 else 1.0

                if var_factor > 1.3:
                    var_text = "**more colorful**"
                elif var_factor < 0.7:
                    var_text = "**more uniform**"
                else:
                    var_text = "**standard variation** in its"

                if sat_factor > 1.5:
                    sat_text = "**exceptionally more vibrant than**"
                elif sat_factor > 1.1:
                    sat_text = f"**{sat_factor:.1f}x more colorful than**"
                elif sat_factor < 0.5:
                    sat_text = "**highly desaturated compared to**"
                elif sat_factor < 0.9:
                    sat_text = f"**{1 / sat_factor:.1f}x more muted than**"
                else:
                    sat_text = "visually consistent with"

                # st.info(
                #     f"{main_info['Game'].title()} is {sat_text} "
                #     f"the average game from the {main_info['Decade']}s."
                # )
                st.info(
                    f"{main_info['Game'].title()} has a {var_text} color palette compared to the average in the {main_info['Decade']}s\n\n"
                    f"Its colors are overall **{sat_text}** the decade average."
                )

        st.divider()

        st.subheader("🖼️ Source Screenshots & Local Palettes")
        cols = st.columns(3)
        screens = get_specific_game_screenshots(selected_game_id)
        for i, row in enumerate(screens.itertuples()):
            with cols[i % 3]:
                st.image(row.Screenshot, width="stretch")

                mini_html = (
                    '<div style="display: flex; height: 30px; border-radius: 6px; '
                    'overflow: hidden; border: 2px solid #555; margin-bottom: 30px; margin-top: -5px;">'
                )

                for j in range(1, 10):
                    r = getattr(row, f"C{j}_R")
                    g = getattr(row, f"C{j}_G")
                    b = getattr(row, f"C{j}_B")
                    if pd.isna(r) or pd.isna(g) or pd.isna(b):
                        continue
                    hex_code = f"#{int(r):02x}{int(g):02x}{int(b):02x}".upper()

                    mini_html += (
                        f'<div title="{hex_code}" '
                        f'style="background-color:{hex_code}; flex:1; cursor: pointer;"></div>'
                    )

                mini_html += "</div>"
                st.markdown(mini_html, unsafe_allow_html=True)

        st.info("💡 TOOL TIP: Hover over any color block to see the specific Hex Code.")
