import os
import streamlit as st
import pandas as pd
import plotly.express as px
import helper_functions as helper
import json

st.set_page_config(
    layout="wide", page_title="Evolution of Color and Art Styles in Video Game Design"
)
# [theme]
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

path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/processed_game_data.parquet"
)
df, unique_devs_list, top_50_global = helper.load_data(path)
df_safe = df[df["is_nsfw"] == False].copy()
# decades = sorted(
#     list(set([(d // 10) * 10 for d in df["Year"].unique() if d >= 1970])), reverse=True
# )
decades = sorted(list(set(df["Decade"].unique())))
# decade_list = sorted(df["Decade"].unique())

if st.session_state.get("trigger_nav"):
    st.session_state["page_selection"] = "Individual Game Palette"
    st.session_state["trigger_nav"] = False

page = st.sidebar.radio(
    "Analysis Tabs",
    [
        "Art Style Popularity",
        "Color through Decades",
        "Genre Timelines",
        "Theme Timelines",
        # "Colorfulness",
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

if page == "Art Style Popularity":
    st.header("📈 Art Style Popularity through Time")
    classified_df = df[df["is_classified"]]
    style_counts = classified_df.groupby(["Year", "Art_Style"]).size().reset_index(name="Count")
    year_totals = classified_df.groupby("Year").size().reset_index(name="Total")
    perc_df = style_counts.merge(year_totals, on="Year")
    perc_df["Percentage"] = (perc_df["Count"] / perc_df["Total"]) * 100

    fig = px.area(
        perc_df,
        x="Year",
        y="Percentage",
        color="Art_Style",
        height=600,
        # category_orders={"Art_Style": sorted(classified_df["Art_Style"].unique())},
    )
    fig.update_yaxes(range=[0, 100])
    fig.update_xaxes(type="linear", range=[1950, 2026])
    fig.update_layout(
        yaxis=dict(
            title_font=dict(size=22),  # Y-axis title
            tickfont=dict(size=20),  # Y-axis numbers (0, 20, 40...)
        ),
        xaxis=dict(
            title_font=dict(size=22),
            tickfont=dict(size=20),
        ),
        legend=dict(
            title="Art Styles",
            font=dict(size=20),
            title_font=dict(size=24),
            itemsizing="constant",  # Keeps the color icons consistent
        ),
        legend_title_side="top center",
        font=dict(size=20),
    )
    st.plotly_chart(fig, width="stretch")

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

    st.info(
        f"We have successfully classified **{classified_total} out of {total_games}** games (**{percent_complete:.1f}%**) using image-based DNA."
    )


elif page == "Color through Decades":
    st.header("🎨 Color through Decades")
    st.subheader("Dominant colors of each decade")
    # st.write("Evolution of the dominant industry palette alongside tech milestones.")

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

    # helper.render_saturation_heatmap(df)

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
        style_df_safe = style_df[style_df["is_nsfw"] == False]
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
    # st.subheader("🕹️ Genre-Specific Evolution")
    st.write("**☝TOOL TIP**: Click the 🔍 tab to expand and see year-by-year breakdowns")
    st.write("☝Hover mouse over the colors in the breakdown to see their hex codes")
    all_genres = sorted(list(set(df["Genres"].str.split("|").explode().str.strip().unique())))
    selected_genre = st.selectbox(
        "Select Genre", [g for g in all_genres if g], key="genre_trace_box"
    )

    if selected_genre:
        genre_df = df[df["Genre_Set"].apply(lambda x: selected_genre.lower() in x)]

        for dec in decades:
            decade_data_g = genre_df[(genre_df["Year"] >= dec) & (genre_df["Year"] < dec + 10)]
            if not decade_data_g.empty:
                valid_styles = decade_data_g[decade_data_g["Art_Style"] != "Unclassified"][
                    "Art_Style"
                ]
                top_style = valid_styles.mode()[0] if not valid_styles.empty else "General Industry"

                palette = helper.get_ranked_colors(decade_data_g, count=10)
                # st.write(f"#### {dec}s Era")
                # st.write(f"Most Common Art Style: {top_style}")
                st.markdown(
                    f"""
                    <div style='line-height: 1.5;'>
                        <span style='font-size: 25px; font-weight: bold;'>{dec}s </span>
                        <span style='font-size: 18px; color: white;'>Most Common Art Style: {top_style}</span>
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
                        col_label.write(f"**{year}** (Games: {formatted_year_count})")
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
                        # helper.render_color_strip(year_data, f"  ↳ {year}", f"{len(year_data)} games")


elif page == "Theme Timelines":
    st.header("🎨 Theme-Specific Color Evolution")
    st.write("**👁👄👁TOOL TIP**: Click the 🔍 tab to expand and see year-by-year breakdowns")
    st.write("💡 Hover mouse over the colors in the breakdown to see their hex codes")

    all_themes = sorted(list(set(df["Themes"].str.split("|").explode().str.strip().unique())))
    selected_theme = st.selectbox(
        "Select Theme", [t for t in all_themes if t], key="theme_trace_box"
    )

    if selected_theme:
        theme_df = df[df["Theme_Set"].apply(lambda x: selected_theme.lower() in x)]

        for dec in decades:
            decade_data_t = theme_df[(theme_df["Year"] >= dec) & (theme_df["Year"] < dec + 10)]
            if not decade_data_t.empty:
                valid_styles = decade_data_t[decade_data_t["Art_Style"] != "Unclassified"][
                    "Art_Style"
                ]
                top_style = valid_styles.mode()[0] if not valid_styles.empty else "General Industry"
                palette = helper.get_ranked_colors(decade_data_t, count=10)

                st.markdown(
                    f"""
                    <div style='line-height: 1.5;'>
                        <span style='font-size: 25px; font-weight: bold;'>{dec}s </span><span style='font-size: 18px; color: white;'>Most Common Art Style: {top_style}</span>
                        
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
                        col_label.write(f"**{year}** (Games: {formatted_year_count})")

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
                st.caption(f"Analyzing {len(all_df)} entries")
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
                    )
                    fig_all.update_layout(
                        showlegend=True,
                        legend=dict(
                            font=dict(size=20),
                        ),
                    )
                    st.plotly_chart(fig_all, width="stretch")

                    # Report Unclassified %
                    unclassified = ((len(all_df) - len(classified_all)) / len(all_df)) * 100
                    st.caption(f"**{unclassified:.1f}%** of portfolio is unclassified.")
                else:
                    st.warning(f"No games by {final_all.title()} were classified.")
                st.info(
                    "TOOL TIP: Hover mouse over the pie chart slices to see the art style names and percentages"
                )

    st.divider()

    st.subheader("📆 Decade-Specific Leaders")
    dec_sel_s = st.selectbox("Pick Decade", [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020])

    decade_df = df[(df["Year"] >= dec_sel_s) & (df["Year"] < dec_sel_s + 10)]

    exploded_dec = decade_df["Developers"].str.split("|").explode().str.strip()
    top_10_dec = exploded_dec[exploded_dec != ""].value_counts().nlargest(10).index.tolist()

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
                            f"**Note:** {unclassified:.1f}% of {final_dec.title()}'s {dec_sel_s}s portfolio is unclassified."
                        )
                    else:
                        st.caption(
                            f"All {final_dec.title()}'s games for this period are classified."
                        )
                else:
                    st.warning(f"No games by {final_dec.title()} were classified for this period.")
                st.info(
                    "TOOL TIP: Hover mouse over the pie chart slices to see the art style names and percentages"
                )
    st.divider()

    st.subheader("⚔️ Studio Head-to-Head Comparison")
    st.write("Directly compare the artistic evolution of two studios within the same decade.")
    st.info(
        "TOOL TIP: You can write in the selectbox fields to quickly find studios by name instead of scrolling through the list."
    )

    decade_comparison = st.select_slider(
        "Select Comparison Decade", options=[1970, 1980, 1990, 2000, 2010, 2020], key="comp_slider"
    )
    compare_df = df[(df["Year"] >= decade_comparison) & (df["Year"] < decade_comparison + 10)]

    active_devs = sorted(
        compare_df["Developers"].str.split("|").explode().str.strip().unique().tolist()
    )
    active_devs = [d for d in active_devs if d]

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
                    style_data.columns = ["Style", "Count"]
                    fig_comp = px.pie(
                        style_data,
                        names="Style",
                        values="Count",
                        hole=0.5,
                        height=350,
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                    )
                    fig_comp.update_layout(showlegend=True, legend=dict(font=dict(size=18)))
                    st.plotly_chart(fig_comp, width="stretch")

                    uncl_comp_pct = ((len(s_df) - len(s_df_classified)) / len(s_df)) * 100
                    st.caption(f"Unclassified: **{uncl_comp_pct:.1f}%**")
                else:
                    st.info("No games were classified")
        st.info(
            "TOOL TIP: Hover mouse over the pie chart slices to see the art style names and percentages"
        )

elif page == "Individual Game Palette":
    st.header("🔍 Individual Game Analysis")
    # st.write("Extracting the visual DNA and metadata for specific titles.")

    unique_games = sorted(df_safe["Unique_ID"].unique())

    if "search_query" in st.session_state:
        st.session_state["game_selector"] = st.session_state["search_query"]
        del st.session_state["search_query"]

    search_query = st.text_input("Filter list by name:", "")
    if search_query:
        filtered_list = [g for g in unique_games if search_query.lower() in g.lower()]
        if not filtered_list:
            st.warning(f"🔍 No games found matching '**{search_query}**'.")
            st.info(
                "TOOL TIP: Check for typos or try a broader term (e.g., 'Zelda' instead of 'The Legend of Zelda: Breath of the Wild')."
            )
            st.stop()
    else:
        filtered_list = unique_games

    # if not filtered_list:
    #     st.warning(f"No games found matching '{search_query}'. Please try a different name.")
    #     st.stop()

    selected_game_id = st.selectbox("Select a game:", filtered_list, key="game_selector")

    if selected_game_id:
        is_nsfw_check = df[df["Unique_ID"] == selected_game_id]["is_nsfw"].any()

        if is_nsfw_check:
            st.warning(
                "⚠️ This title has been filtered from visual display due to content maturity settings."
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

            dna_string = main_info["Precalc_DNA"]

            html_dna = '<div style="display: flex; height: 100px; border-radius: 12px; overflow: hidden;border: 3px solid #999; ">'
            for entry in dna_string.split("|"):
                color, weight = entry.split(",")
                # html_dna += f'<div style="background-color:{color}; flex:{weight};"></div>'
                html_dna += f'''
                    <div title="{color.upper()}" 
                        style="background-color:{color}; flex:{weight}; "cursor: pointer;">
                    </div>'''
            html_dna += "</div>"
            st.markdown(html_dna, unsafe_allow_html=True)
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
            st.info("💡 TOOL TIP: Hover over the colors to see their hex codes")

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
    st.info("💡 TOOL TIP: Hover over the colors to see their hex codes")
