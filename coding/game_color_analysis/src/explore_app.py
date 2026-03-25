import os
import streamlit as st
import pandas as pd
import plotly.express as px
import helper_functions as helper

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

# @st.cache_data
# def load_summary():
#     return pd.read_parquet(
#         os.path.join(
#             os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/game_summary.parquet"
#         )
#     )


df, unique_devs_list, top_50_global = helper.load_data("data/current_game_data.csv")
# df_summary = load_summary()

if "page_selection" not in st.session_state:
    st.session_state["page_selection"] = "Art Style Popularity"
if st.session_state.get("trigger_nav"):
    st.session_state["page_selection"] = "Game Search MIX"
    st.session_state["trigger_nav"] = False

# --- 3. UI TABS ---
page = st.sidebar.radio(
    "Analysis Tabs",
    [
        "Art Style Popularity",
        "Color through Decades",
        "Genre Timelines",
        "Theme Timelines",
        "Aesthetic Mapping",
        "Studio DNA",
        "Game Search",
        "Game Search MIX",
        "game search 3.0",
        "Innovation & Impact",
    ],
    key="page_selection",
)
if st.sidebar.button("🎲 Random Game"):
    random_game = df["Game"].sample(1).iloc[0]
    st.session_state["search_query"] = random_game
    st.session_state["trigger_nav"] = True
    st.rerun()


if page == "Art Style Popularity":
    st.header("📈 Art Style Popularity through Time")
    classified_df = df[~df["Art_Style"].str.contains("Unclassified", case=False, na=False)]
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
    all_games_decade = df.groupby("Decade")["Game"].nunique().reset_index(name="Total_Games")
    classified_decade = (
        classified_df.groupby("Decade")["Game"].nunique().reset_index(name="Classified_Games")
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

    total_games = df["Game"].nunique()
    classified_total = classified_df["Game"].nunique()
    percent_complete = (classified_total / total_games) * 100

    st.info(
        f"We have successfully classified **{classified_total} out of {total_games}** games (**{percent_complete:.1f}%**) using image-based DNA."
    )


elif page == "Color through Decades":
    st.header("🎨 Palette Archetypes & Technological Milestones")
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

    for dec in [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]:
        dec_df = df[(df["Year"] >= dec) & (df["Year"] < dec + 10)]
        if not dec_df.empty:
            pal = helper.get_representative_palette(dec_df, count=10)

            c1, c2, c3 = st.columns([1, 2, 6])
            c1.write(f"### {dec}s")
            c2.info(milestones.get(dec, ""))

            with c3:
                html = '<div style="display: flex; height: 50px; border-radius: 8px; overflow: hidden; border: 1px solid #333; margin-bottom: 25px;">'
                for color in pal:
                    html += f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")

    # helper.render_saturation_heatmap(df)

    st.subheader("Deep Dive: Style x Decade")
    col_decade, col_style = st.columns(2)
    with col_decade:
        decade_sel = st.select_slider(
            "Select Decade", options=[1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
        )
    with col_style:
        df_decade = df[(df["Year"] >= decade_sel) & (df["Year"] < decade_sel + 10)]
        available_styles = sorted(df_decade["Art_Style"].unique().tolist())
        style_choice = st.selectbox("Art Styles", ["Overall Industry"] + available_styles)

    style_df = df_decade.copy()
    if style_choice != "Overall Industry":
        style_df = df_decade[df_decade["Art_Style"] == style_choice]

    if not style_df.empty:
        palette = helper.get_representative_palette(style_df, count=10)
        p_cols = st.columns(10)
        for i, color in enumerate(palette):
            p_cols[i].markdown(
                f"<div style='background-color:{color}; height:60px; border-radius:5px;'></div>",
                unsafe_allow_html=True,
            )
            p_cols[i].caption(color)

        st.subheader("Visual Sample")
        samples = style_df.sample(min(4, len(style_df)))
        scols = st.columns(4)
        for i, row in enumerate(samples.itertuples()):
            with scols[i % 4]:
                st.image(row.Screenshot, width="stretch")
                st.markdown(
                    f"<div style='font-size:18px; text-align:center; color:gray;'>"
                    f"<b>{row.Game}</b> ({row.Year})"
                    f"</div>",
                    unsafe_allow_html=True,
                )


elif page == "Genre Timelines":
    st.header("📅 Historical Color Strip")
    st.write("Analyze visual identities across decades with a detailed year-by-year drill-down.")

    st.subheader("🕹️ Genre-Specific Evolution")
    all_genres = sorted(list(set(df["Genres"].str.split("|").explode().str.strip().unique())))
    sel_genre = st.selectbox(
        "Select Genre to Trace", [g for g in all_genres if g], key="genre_trace_box"
    )

    if sel_genre:
        # Pooled filtering logic
        g_df = df[df["Genres"].str.contains(rf"\b{sel_genre}\b", case=False, na=False, regex=True)]

        # Iterate through Decades
        decades = sorted([d for d in g_df["Year"].unique() if d >= 1970], reverse=True)
        unique_decades = sorted(list(set([(d // 10) * 10 for d in decades])), reverse=True)

        for dec in unique_decades:
            dec_subset = g_df[(g_df["Year"] >= dec) & (g_df["Year"] < dec + 10)]
            if not dec_subset.empty:
                # Main Decade Header
                helper.render_color_strip(
                    dec_subset, f"{dec}s Era", f"Market Share: {dec_subset['Art_Style'].mode()[0]}"
                )

                # Expandable Year Detail
                with st.expander(f"🔍 View Year-by-Year breakdown for the {dec}s"):
                    year_list = sorted(dec_subset["Year"].unique(), reverse=True)
                    for yr in year_list:
                        yr_subset = dec_subset[dec_subset["Year"] == yr]
                        helper.render_color_strip(yr_subset, f"  ↳ {yr}", f"{len(yr_subset)} games")


elif page == "Theme Timelines":
    st.header("📅 Theme-Based Color Evolution")
    st.write("Explore how visual styles evolved across different themes over time.")

    st.subheader("🎭 Theme-Specific Evolution")
    all_themes = sorted(list(set(df["Themes"].str.split("|").explode().str.strip().unique())))
    sel_theme = st.selectbox(
        "Select Theme to Trace", [t for t in all_themes if t], key="theme_trace_box"
    )

    if sel_theme:
        t_df = df[df["Themes"].str.contains(rf"\b{sel_theme}\b", case=False, na=False, regex=True)]

        t_decades = sorted(
            list(set([(d // 10) * 10 for d in t_df["Year"].unique() if d >= 1970])), reverse=True
        )

        for dec in t_decades:
            t_dec_subset = t_df[(t_df["Year"] >= dec) & (t_df["Year"] < dec + 10)]
            if not t_dec_subset.empty:
                helper.render_color_strip(
                    t_dec_subset,
                    f"{dec}s Theme",
                    f"Avg Saturation: {t_dec_subset['saturation'].mean():.1f}",
                )

                with st.expander(f"🔍 Detail: {sel_theme.title()} in the {dec}s"):
                    t_year_list = sorted(t_dec_subset["Year"].unique(), reverse=True)
                    for yr in t_year_list:
                        t_yr_subset = t_dec_subset[t_dec_subset["Year"] == yr]
                        helper.render_color_strip(
                            t_yr_subset, f"  ↳ {yr}", f"{len(t_yr_subset)} titles"
                        )


elif page == "Aesthetic Mapping":
    st.header("📍 The Visual Landscape")

    # --- SIDEBAR UI ---
    with st.sidebar:
        st.subheader("🎨 Research Filters")
        all_genres_list = sorted(set(df["Genres"].str.split("|").explode().dropna().unique()))
        genre_toggle = st.toggle("Select All Genres", value=True)
        selected_genres = (
            all_genres_list if genre_toggle else st.multiselect("Pick Genres", all_genres_list)
        )

        all_styles = sorted(df["Art_Style"].dropna().unique().tolist())
        style_toggle = st.toggle("Select All Art Styles", value=True)
        selected_styles = (
            all_styles if style_toggle else st.multiselect("Pick Specific Styles", all_styles)
        )

    if selected_genres:
        # Non-Regex Piped Genre Filter
        def genre_filter(genre_string):
            if pd.isna(genre_string):
                return False
            game_genres = genre_string.split("|")
            return any(g in selected_genres for g in game_genres)

        mask = (df["Genres"].apply(genre_filter)) & (df["Art_Style"].isin(selected_styles))
        plot_df = df[mask & (df["Year"] >= 1980)].copy()

        plot_df["Decade"] = (plot_df["Year"] // 10 * 10).astype(int).astype(str) + "s"
        decade_list = sorted(plot_df["Decade"].unique())

        # 0-100 Normalization
        plot_df["lum_pct"] = plot_df["luminance"] * 100
        plot_df["sat_pct"] = (plot_df["saturation"] / plot_df["saturation"].max()) * 100
        plot_df["hex_color"] = plot_df.apply(
            lambda r: f"#%02x%02x%02x" % (int(r["C1_R"]), int(r["C1_G"]), int(r["C1_B"])), axis=1
        )

        if not plot_df.empty:
            fig = px.scatter(
                plot_df,
                x="lum_pct",
                y="sat_pct",
                hover_name="Game",
                facet_col="Decade",
                facet_col_wrap=3,
                category_orders={"Decade": decade_list},
                labels={"lum_pct": "Brightness", "sat_pct": "Colorfulness"},
                range_x=[-5, 105],
                range_y=[-5, 105],
                template="plotly_dark",
            )

            # Drop opacity further to make background "recede"
            fig.update_traces(marker=dict(color=plot_df["hex_color"], size=4, opacity=0.25))

            # --- ANNOTATION-BASED STARS (Guaranteed Visibility) ---
            centroids = plot_df.groupby("Decade")[["lum_pct", "sat_pct"]].mean().reset_index()

            for i, decade in enumerate(decade_list):
                dec_avg = centroids[centroids["Decade"] == decade]
                if not dec_avg.empty:
                    # Annotations use 'xref' and 'yref' to target specific facets
                    # 'x1', 'y1' for first facet, 'x2', 'y2' for second, etc.
                    ref_idx = i + 1

                    fig.add_annotation(
                        x=dec_avg["lum_pct"].iloc[0],
                        y=dec_avg["sat_pct"].iloc[0],
                        xref=f"x{ref_idx}",
                        yref=f"y{ref_idx}",
                        text="⭐",  # Using an emoji for absolute layering priority
                        showarrow=False,
                        font=dict(size=24),  # Large and bright
                        bgcolor="rgba(0,0,0,0.5)",  # Dark halo to pop against dots
                        borderpad=2,
                    )

            fig.update_layout(height=450 * ((len(decade_list) + 2) // 3), margin=dict(t=50, b=50))
            st.plotly_chart(fig, width="stretch")
            st.info(
                "💡 **How to read this:** The **Star** shows the typical 'look' of the decade. Notice how the star moves toward the bottom-left during the 2000s—this represents the industry-wide shift toward grittier, browner palettes."
            )

# --- TAB: STUDIO DNA ---
elif page == "Studio DNA":
    st.header("🏢 Studio Visual Fingerprints")
    st.write(
        "Analysis of developer-specific color identities and stylistic preferences across their portfolio."
    )

    # Section 1: All-Time Giants (Pooled Data)
    st.subheader("🏆 All-Time Industry Giants")

    # We use the top_50_global list which was pre-calculated by exploding the pipe strings
    col1, col2 = st.columns([1, 2])
    with col1:
        sel_all = st.selectbox("Major Studio", ["Select..."] + top_50_global, key="all_time_box")
        search_all = st.text_input(
            "Or search name:",
            "",
            key="all_search",
            help="Finds any game where this studio is listed.",
        )

        final_all = search_all if search_all else (sel_all if sel_all != "Select..." else None)

    if final_all:
        # regex=True with \b ensures we find 'nintendo' in 'nintendo|tose' but not 'supernintendo'
        all_df = df[
            df["Developers"].str.contains(rf"\b{final_all}\b", case=False, na=False, regex=True)
        ]

        with col2:
            st.write(f"### Palette Signature: {final_all.title()}")
            st.caption(f"Analyzing {len(all_df)} pooled entries")
            p_all = helper.get_representative_palette(all_df, count=10)

            # Horizontal Palette Bar
            html_bar = '<div style="display: flex; height: 40px; border-radius: 8px; overflow: hidden; border: 1px solid #333; margin-bottom: 20px;">'
            for color in p_all:
                html_bar += f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
            html_bar += "</div>"
            st.markdown(html_bar, unsafe_allow_html=True)

            detail_col1, detail_col2 = st.columns(2)
            with detail_col1:
                st.plotly_chart(
                    px.pie(
                        all_df, names="Art_Style", hole=0.4, height=350, title="Style Distribution"
                    ),
                    width="stretch",
                )
            with detail_col2:
                st.write("#### Core Palette Details")
                for c in p_all[:8]:
                    st.markdown(
                        f'<div style="background-color:{c}; padding:5px 10px; border-radius:4px; color:white; font-family:monospace; margin-bottom:2px; font-size:0.9em; border:1px solid #444;">{c}</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    # Section 2: Decade-Specific Leaders
    st.subheader("⏳ Decade-Specific Leaders")
    dec_sel_s = st.selectbox("Pick Decade", [1970, 1980, 1990, 2000, 2010, 2020])

    # Filter the main DF for the decade first
    dec_df_full = df[(df["Year"] >= dec_sel_s) & (df["Year"] < dec_sel_s + 10)]

    # Explode the developers for this decade specifically to find the true leaders
    exploded_dec = dec_df_full["Developers"].str.split("|").explode().str.strip()
    top_15_dec = exploded_dec[exploded_dec != ""].value_counts().nlargest(15).index.tolist()

    col3, col4 = st.columns([1, 2])
    with col3:
        sel_dec = st.selectbox(
            f"Top Studios of the {dec_sel_s}s", ["Select..."] + top_15_dec, key="dec_box"
        )
        search_dec = st.text_input("Or search decade studio:", "", key="dec_search")
        final_dec = search_dec if search_dec else (sel_dec if sel_dec != "Select..." else None)

    if final_dec:
        dec_dev_df = dec_df_full[
            dec_df_full["Developers"].str.contains(
                rf"\b{final_dec}\b", case=False, na=False, regex=True
            )
        ]
        with col4:
            st.write(f"### {final_dec.title()}'s Style in the {dec_sel_s}s")
            p_dec = helper.get_representative_palette(dec_dev_df, count=10)

            html_bar_dec = '<div style="display: flex; height: 40px; border-radius: 8px; overflow: hidden; border: 1px solid #333; margin-bottom: 20px;">'
            for color in p_dec:
                html_bar_dec += (
                    f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
                )
            html_bar_dec += "</div>"
            st.markdown(html_bar_dec, unsafe_allow_html=True)

            detail_col3, detail_col4 = st.columns(2)
            with detail_col3:
                fig_bar = px.bar(
                    dec_dev_df.groupby("Art_Style").size().reset_index(name="Count"),
                    x="Art_Style",
                    y="Count",
                    color="Art_Style",
                    title="Technique Volume",
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, width="stretch")
            with detail_col4:
                st.write("#### Hex Detail")
                for c in p_dec[:8]:
                    st.markdown(
                        f'<div style="background-color:{c}; padding:4px 10px; border-radius:4px; color:white; font-family:monospace; margin-bottom:2px; font-size:0.8em; border:1px solid #444;">{c}</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    # Section 3: Studio Head-to-Head Comparison
    st.subheader("⚔️ Studio Head-to-Head Comparison")
    st.write("Directly compare the artistic evolution of two studios within the same decade.")

    comp_dec = st.select_slider(
        "Select Comparison Decade", options=[1970, 1980, 1990, 2000, 2010, 2020], key="comp_slider"
    )
    comp_df = df[(df["Year"] >= comp_dec) & (df["Year"] < comp_dec + 10)]

    # Extract unique pooled developers for this decade
    active_devs = sorted(
        comp_df["Developers"].str.split("|").explode().str.strip().unique().tolist()
    )
    active_devs = [d for d in active_devs if d]  # Remove empties

    ca, cb = st.columns(2)
    with ca:
        studio_a = st.selectbox("Studio A", active_devs, index=0)
    with cb:
        studio_b = st.selectbox("Studio B", active_devs, index=min(1, len(active_devs) - 1))

    if studio_a and studio_b:
        res_a, res_b = st.columns(2)
        for studio_name, col in [(studio_a, res_a), (studio_b, res_b)]:
            # Filter using the pooled regex logic
            s_df = comp_df[
                comp_df["Developers"].str.contains(
                    rf"\b{studio_name}\b", case=False, na=False, regex=True
                )
            ]

            with col:
                st.write(f"#### {studio_name.title()}")
                st.caption(f"{len(s_df)} games analyzed")
                pal = helper.get_representative_palette(s_df, count=8)

                html_comp = '<div style="display: flex; height: 35px; border-radius: 6px; overflow: hidden; border: 1px solid #333; margin-bottom: 15px;">'
                for color in pal:
                    html_comp += f'<div style="background-color:{color}; flex:1;"></div>'
                html_comp += "</div>"
                st.markdown(html_comp, unsafe_allow_html=True)

                style_data = s_df["Art_Style"].value_counts().reset_index()
                style_data.columns = ["Style", "Count"]
                fig_comp = px.pie(style_data, names="Style", values="Count", hole=0.5, height=280)
                fig_comp.update_layout(showlegend=False)
                st.plotly_chart(fig_comp, width="stretch")

elif page == "Game Search":
    st.header("🔍 Individual Game Analysis")
    st.write("Search for a game to see its aggregated visual identity across all screenshots.")

    # 1. Use .unique() to fix the duplicate game name issue
    unique_games = sorted(df["Game"].unique())
    selected_game = st.selectbox("Select a game from your dataset:", unique_games)

    if selected_game:
        # 2. Filter data for THIS specific game
        game_rows = df[df["Game"] == selected_game]

        col1, col2 = st.columns([1, 2])

        with col1:
            st.write(f"### Metadata")
            st.write(f"**Year:** {game_rows.iloc[0]['Year']}")
            st.write(f"**Studio:** {game_rows.iloc[0]['Developers'].title()}")
            st.write(f"**Style:** {game_rows.iloc[0]['Art_Style']}")
            st.write(f"**Screenshots Analyzed:** {len(game_rows)}")

        with col2:
            st.write("### Aggregated Game Palette")
            st.caption("Averaged colors across all game screenshots (Weighted by dominance)")

            # 3. Aggregate colors. We iterate 1-10 because main.py now has 10 colors.
            game_pal_list = []
            for i in range(1, 11):
                # We calculate the average R, G, B, and Weight for each cluster slot across all rows
                r = game_rows[f"C{i}_R"].mean()
                g = game_rows[f"C{i}_G"].mean()
                b = game_rows[f"C{i}_B"].mean()
                w = game_rows[f"C{i}_W"].mean()
                if not pd.isna(r):
                    game_pal_list.append((r, g, b, w))

            # Sort by weight so most important colors are first
            game_pal_list.sort(key=lambda x: x[3], reverse=True)

            # 4. Draw the Palette Bar
            html_bar = '<div style="display: flex; height: 80px; border-radius: 10px; overflow: hidden; border: 2px solid #555;">'
            for r, g, b, w in game_pal_list:
                if w > 0:
                    html_bar += f'<div style="background-color:rgb({int(r)},{int(g)},{int(b)}); flex:{w};" title="Weight: {w:.1%}"></div>'
            html_bar += "</div>"
            st.markdown(html_bar, unsafe_allow_html=True)

        st.divider()

        # 5. Show the individual screenshots analyzed
        st.write("### Source Screenshots")
        img_cols = st.columns(len(game_rows))
        for i, row in enumerate(game_rows.itertuples()):
            img_cols[i].image(row.Screenshot, width="stretch")
            # Mini palette for each individual screen
            mini_pal = ""
            for j in range(1, 6):  # Just show first 5 for the small preview
                r, g, b = getattr(row, f"C{j}_R"), getattr(row, f"C{j}_G"), getattr(row, f"C{j}_B")
                if not pd.isna(r):
                    mini_pal += f'<div style="background-color:rgb({int(r)},{int(g)},{int(b)}); height:10px; flex:1;"></div>'
            img_cols[i].markdown(
                f'<div style="display:flex;">{mini_pal}</div>', unsafe_allow_html=True
            )
elif page == "game search 3.0":
    st.header("🔍 Individual Game Analysis")
    st.write("Search for a specific title to extract its unique visual DNA and metadata.")

    # Search Bar with Autocomplete-like behavior
    search_query = st.text_input("Type game name:", placeholder="e.g. Super Mario World").lower()

    if search_query:
        # Filter for the specific game
        game_data = df[df["Game"].str.contains(search_query, case=False, na=False)]

        if not game_data.empty:
            # Handle multiple results by letting the user select the exact one
            if len(game_data) > 1:
                st.warning(f"Found {len(game_data)} matches. Please refine your selection:")
                selected_game_name = st.selectbox(
                    "Select the exact game:", game_data["Game"].tolist()
                )
                selected_game = game_data[game_data["Game"] == selected_game_name].iloc[0]
            else:
                selected_game = game_data.iloc[0]

            st.divider()

            # --- DISPLAY SECTION ---
            col1, col2 = st.columns([1, 2])

            with col1:
                if "Screenshot" in selected_game and pd.notna(selected_game["Screenshot"]):
                    st.image(selected_game["Screenshot"], width="stretch")
                else:
                    st.info("No image available for this title.")

                # # Technical Visual Specs
                # st.subheader("📊 Visual Specs")
                # st.metric("Luminance (Brightness)", f"{selected_game['luminance'] * 100:.1f}%")
                # st.metric("Saturation (Vibrancy)", f"{selected_game['saturation']:.1f}")

            with col2:
                st.title(selected_game["Game"].title())

                # Metadata Grid
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    st.markdown(f"**📅 Year:** {selected_game['Year']}")
                    st.markdown(
                        f"**🏢 Developer:** {selected_game['Developers'].replace('|', ', ').title()}"
                    )
                    st.markdown(f"**🎨 Art Style:** {selected_game['Art_Style']}")

                with m_col2:
                    st.markdown(
                        f"**🕹️ Genres:** {selected_game['Genres'].replace('|', ', ').title()}"
                    )
                    st.markdown(
                        f"**🎭 Themes:** {selected_game['Themes'].replace('|', ', ').title()}"
                    )

                # Game-Specific Palette Generation
                st.subheader("🎨 Representative Palette")
                # We use the existing engine but pass only this single game's data
                game_subset = df[df["Game"] == selected_game["Game"]]
                game_pal = helper.get_representative_palette(game_subset, count=5)

                html_pal = '<div style="display: flex; height: 80px; border-radius: 10px; overflow: hidden; border: 2px solid #444; margin-top: 10px;">'
                for color in game_pal:
                    html_pal += (
                        f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
                    )
                html_pal += "</div>"
                st.markdown(html_pal, unsafe_allow_html=True)

                # Hex Code List for copy-pasting
                st.caption("Hex codes: " + ", ".join(game_pal))

            st.divider()

            # Contextual Comparison
            st.subheader(
                f"How {selected_game['Game'].title()} compares to the {selected_game['Decade']}"
            )
            dec_avg_sat = df[df["Decade"] == selected_game["Decade"]]["saturation"].mean()
            diff = selected_game["saturation"] - dec_avg_sat

            status = "more colorful" if diff > 0 else "more muted"
            st.write(
                f"This game is **{abs(diff):.1f} units {status}** than the average game from the {selected_game['Decade']}."
            )

        else:
            st.error("No game found with that name. Try a different keyword.")
elif page == "Game Search MIX":
    st.header("🔍 Individual Game Analysis")
    st.write("Extracting the visual DNA and metadata for specific titles.")

    # Check if we arrived here from a click in the Deep Dive section
    default_game = st.session_state.get("search_query")

    # Combined Search: Selectbox with unique names for accuracy
    unique_games = sorted(df["Game"].unique())
    default_index = 0
    if default_game in unique_games:
        default_index = unique_games.index(default_game)
    selected_game_name = st.selectbox("Select or search a game:", unique_games, index=default_index)
    # selected_game = st.selectbox("Search for a game:", [""] + unique_games)
    if "search_query" in st.session_state:
        del st.session_state["search_query"]

    if selected_game_name:
        # Filter for all rows belonging to this game
        game_rows = df[df["Game"] == selected_game_name]
        main_info = game_rows.iloc[0]

        st.divider()

        # --- TOP SECTION: Metadata & Technical Stats ---
        col1, col2 = st.columns([1.5, 2])

        with col1:
            st.title(main_info["Game"].title())
            st.markdown(f"**📅 Year:** {main_info['Year']}")
            st.markdown(f"**🏢 Studio:** {main_info['Developers'].replace('|', ', ').title()}")
            st.markdown(f"**🎨 Art Style:** {main_info['Art_Style']}")
            st.markdown(f"**🕹️ Genres:** {main_info['Genres'].replace('|', ', ').title()}")
            st.markdown(f"**🖼️ Screenshots:** {len(game_rows)} images")

        # with col3:
        #     st.subheader("📊 Visual Specs")
        #     st.metric("Brightness", f"{game_meta['luminance'] * 100:.1f}%")
        #     st.metric("Vibrancy", f"{game_meta['saturation']:.1f}")
        #     st.caption(f"Based on {len(game_rows)} screens")

        with col2:
            st.subheader("🎨 Representative Palette")
            game_pal = helper.get_representative_palette(game_rows, count=10)

            html_pal = '<div style="display: flex; height: 80px; border-radius: 10px; overflow: hidden; border: 2px solid #555;">'
            for color in game_pal:
                html_pal += f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
            html_pal += "</div>"
            st.markdown(html_pal, unsafe_allow_html=True)
            st.caption(f"Hex: {', '.join(game_pal)}")

        # --- MIDDLE SECTION: Historical Context ---
        # 1. Calculate the Decade Average Saturation
        decade_avg_sat = df[df["Decade"] == main_info["Decade"]]["saturation"].mean()
        factor = main_info["saturation"] / decade_avg_sat

        if factor > 1.2:  # Significantly more
            comparison_text = f"**{factor:.1f}x more colorful**"
        elif factor < 0.8:  # Significantly less
            comparison_text = f"**{1 / factor:.1f}x more muted**"
        else:
            comparison_text = "roughly consistent with"

        st.info(
            f"**Thesis Context:** {main_info['Game'].title()} is {comparison_text} "
            f"than the average game from the {main_info['Decade']}."
        )

        st.divider()

        # --- BOTTOM SECTION: Source Screenshots Grid ---
        st.subheader("🖼️ Source Screenshots")
        # Dynamic columns based on number of screenshots (max 5 per row)
        n_screens = len(game_rows)
        cols = st.columns(min(n_screens, 5))

        for i, row in enumerate(game_rows.itertuples()):
            with cols[i % 5]:
                st.image(row.Screenshot, width="stretch")
                single_img_data = game_rows[game_rows["Screenshot"] == row.Screenshot]
                screen_pal = helper.get_representative_palette(single_img_data, count=5)

                mini_html = '<div style="display: flex; height: 12px; margin-top: -10px; border-radius: 0 0 5px 5px; overflow: hidden; border: 1px solid #333;">'
                for color in screen_pal:
                    mini_html += (
                        f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
                    )
                mini_html += "</div>"

                st.markdown(mini_html, unsafe_allow_html=True)

        st.write("Each image shows its specific 5-color palette below it.")
