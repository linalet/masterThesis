import os
import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config for a wider layout
st.set_page_config(layout="wide", page_title="Video Game Color Thesis")
studio_map = {
    "nintendo": [
        "nintendo r&d",
        "nintendo ead",
        "nintendo entertainment",
        "nintendo ird",
        "nintendo tokyo",
    ],
    "ubisoft": [
        "ubi soft",
        "ubisoft montreal",
        "ubisoft toronto",
        "ubisoft paris",
        "ubisoft entertainment",
    ],
    "sega": ["sega am", "sega wow", "sega technical institute", "sonic team"],
    "capcom": ["capcom production", "capcom development"],
    "konami": ["konami computer entertainment", "konami tokyo", "konami osaka"],
}


# --- 1. DATA LOADING & TAXONOMY ---
@st.cache_data
def load_data():
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/test_game_data.csv"
    )
    df = pd.read_csv(csv_path)

    for col in ["Genres", "Themes", "Keywords", "Developers", "Game"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
    df["Developers"] = df["Developers"].fillna("").astype(str).str.lower()

    # B. Normalization Helper
    def normalize_studio_name(dev_string):
        # Split pipe-connected studios first
        parts = [p.strip() for p in dev_string.split("|")]
        cleaned_parts = []

        for part in parts:
            found_parent = False
            for parent, aliases in studio_map.items():
                # If the part is exactly the parent or contains any of the alias keywords
                if part == parent or any(alias in part for alias in aliases):
                    cleaned_parts.append(parent)
                    found_parent = True
                    break
            if not found_parent:
                cleaned_parts.append(part)

        # Return joined string to keep original data structure for pooling
        return "|".join(list(set(cleaned_parts)))

    df["Developers"] = df["Developers"].apply(normalize_studio_name)

    # C. Proceed with Pooling logic
    all_devs_series = df["Developers"].str.split("|").explode().str.strip()
    # Now top_studios_global will correctly count ALL Nintendo divisions as "nintendo"
    top_studios_global = (
        all_devs_series[all_devs_series != ""].value_counts().nlargest(50).index.tolist()
    )
    unique_devs = sorted(all_devs_series[all_devs_series != ""].unique().tolist())

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

        # Fallback to avoid 'Non-Classified'
        if row["Year"] < 1980:
            return "Abstraction: Minimalist"
        return "Realism: Stylized Realism"

    df["Art_Style"] = df.apply(classify_taxonomy, axis=1)
    df["saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )
    return df[df["Year"] > 1950].copy(), unique_devs, top_studios_global


df, unique_devs_list, top_50_global = load_data()


# --- 2. THE SATURATED PALETTE ENGINE ---
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


# --- 3. UI TABS ---
page = st.sidebar.radio(
    "Analysis Tabs", ["Market Trends (%)", "Color Archetypes", "Studio DNA", "Genre Timelines"]
)

# --- TAB: COLOR ARCHETYPES ---
if page == "Color Archetypes":
    st.header("🎨 Palette Archetypes & Technological Milestones")

    render_saturation_heatmap(df)

    # --- NEW: THE HISTORICAL COLOR PILLAR ---
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

    # Generate a row for every decade in one view
    for dec in [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]:
        dec_df = df[(df["Year"] >= dec) & (df["Year"] < dec + 10)]
        if not dec_df.empty:
            pal = get_representative_palette(dec_df, count=10)

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

    # --- EXISTING: DRILL DOWN SECTION ---
    st.subheader("Deep Dive: Style x Decade")
    col_x, col_y = st.columns(2)
    with col_x:
        decade_sel = st.select_slider(
            "Select Decade for Samples", options=[1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
        )
    with col_y:
        style_choice = st.selectbox(
            "Focus Area", ["Overall Industry"] + sorted(df["Art_Style"].unique().tolist())
        )

    f_df = df[(df["Year"] >= decade_sel) & (df["Year"] < decade_sel + 10)]
    if style_choice != "Overall Industry":
        f_df = f_df[f_df["Art_Style"] == style_choice]

    if not f_df.empty:
        palette = get_representative_palette(f_df, count=8)
        p_cols = st.columns(8)
        for i, color in enumerate(palette):
            p_cols[i].markdown(
                f"<div style='background-color:{color}; height:60px; border-radius:5px;'></div>",
                unsafe_allow_html=True,
            )
            p_cols[i].caption(color)

        st.subheader("Visual Sample")
        samples = f_df.sample(min(4, len(f_df)))
        scols = st.columns(4)
        for i, row in enumerate(samples.itertuples()):
            scols[i].image(row.Screenshot, caption=f"{row.Game} ({row.Year})", width="stretch")

# --- TAB: MARKET TRENDS ---
elif page == "Market Trends (%)":
    st.header("📈 Art Style Market Share")
    style_counts = df.groupby(["Year", "Art_Style"]).size().reset_index(name="Count")
    year_totals = df.groupby("Year").size().reset_index(name="Total")
    perc_df = style_counts.merge(year_totals, on="Year")
    perc_df["Percentage"] = (perc_df["Count"] / perc_df["Total"]) * 100

    fig = px.area(perc_df, x="Year", y="Percentage", color="Art_Style", height=600)
    fig.update_yaxes(range=[0, 100])
    fig.update_xaxes(type="linear", range=[1950, 2026])
    st.plotly_chart(fig, width="stretch")
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
            p_all = get_representative_palette(all_df, count=10)

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
                    use_container_width=True,
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
            p_dec = get_representative_palette(dec_dev_df, count=10)

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
                st.plotly_chart(fig_bar, use_container_width=True)
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
                pal = get_representative_palette(s_df, count=8)

                html_comp = '<div style="display: flex; height: 35px; border-radius: 6px; overflow: hidden; border: 1px solid #333; margin-bottom: 15px;">'
                for color in pal:
                    html_comp += f'<div style="background-color:{color}; flex:1;"></div>'
                html_comp += "</div>"
                st.markdown(html_comp, unsafe_allow_html=True)

                style_data = s_df["Art_Style"].value_counts().reset_index()
                style_data.columns = ["Style", "Count"]
                fig_comp = px.pie(style_data, names="Style", values="Count", hole=0.5, height=280)
                fig_comp.update_layout(showlegend=False)
                st.plotly_chart(fig_comp, use_container_width=True)

    # Section 2: Decade Leaders
    st.subheader("⏳ Decade-Specific Leaders")
    dec_sel_s = st.selectbox("Pick Decade for Leaders", [1970, 1980, 1990, 2000, 2010, 2020])
    dec_df_full = df[(df["Year"] >= dec_sel_s) & (df["Year"] < dec_sel_s + 10)]
    top_15_dec = dec_df_full["Developers"].value_counts().nlargest(15).index.tolist()

    col3, col4 = st.columns([1, 2])
    with col3:
        sel_dec = st.selectbox(
            f"Top Studios of the {dec_sel_s}s", ["Select..."] + top_15_dec, key="dec_box"
        )
        search_dec = st.text_input("Or search decade studio:", "", key="dec_search")
        final_dec = search_dec if search_dec else (sel_dec if sel_dec != "Select..." else None)

    if final_dec:
        dec_dev_df = dec_df_full[
            dec_df_full["Developers"].str.contains(final_dec, case=False, na=False)
        ]
        with col4:
            st.write(f"### {final_dec.title()}'s Style in the {dec_sel_s}s")
            p_dec = get_representative_palette(dec_dev_df, count=10)

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
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            with detail_col4:
                st.write("#### Hex Detail")
                for c in p_dec[:8]:
                    st.markdown(
                        f'<div style="background-color:{c}; padding:4px 10px; border-radius:4px; color:white; font-family:monospace; margin-bottom:2px; font-size:0.8em; border:1px solid #444;">{c}</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    # --- SECTION 3: STUDIO HEAD-TO-HEAD ---
    st.subheader("⚔️ Studio Head-to-Head Comparison")
    st.write("Compare the artistic intent and palette of two studios within the same decade.")

    comp_dec = st.select_slider(
        "Select Comparison Decade", options=[1970, 1980, 1990, 2000, 2010, 2020], key="comp_slider"
    )
    comp_df = df[(df["Year"] >= comp_dec) & (df["Year"] < comp_dec + 10)]

    # Get all developers active in this decade
    active_devs = sorted(comp_df["Developers"].unique().tolist())

    ca, cb = st.columns(2)
    with ca:
        studio_a = st.selectbox("Studio A", active_devs, index=0)
    with cb:
        # Default to index 1 if available
        default_b = 1 if len(active_devs) > 1 else 0
        studio_b = st.selectbox("Studio B", active_devs, index=default_b)

    if studio_a and studio_b:
        df_a = comp_df[comp_df["Developers"] == studio_a]
        df_b = comp_df[comp_df["Developers"] == studio_b]

        res_a, res_b = st.columns(2)

        for studio_name, studio_df, col in [(studio_a, df_a, res_a), (studio_b, df_b, res_b)]:
            with col:
                st.write(f"#### {studio_name.title()}")
                pal = get_representative_palette(studio_df, count=8)

                # Comparison Palette Bar
                html_comp = '<div style="display: flex; height: 30px; border-radius: 4px; overflow: hidden; border: 1px solid #333; margin-bottom: 10px;">'
                for color in pal:
                    html_comp += f'<div style="background-color:{color}; flex:1;"></div>'
                html_comp += "</div>"
                st.markdown(html_comp, unsafe_allow_html=True)

                # Style Breakdown
                style_data = studio_df["Art_Style"].value_counts().reset_index()
                style_data.columns = ["Style", "Count"]
                fig_comp = px.pie(style_data, names="Style", values="Count", hole=0.5, height=250)
                fig_comp.update_layout(showlegend=False)
                st.plotly_chart(fig_comp, use_container_width=True)
# --- TAB: GENRE TIMELINES ---
elif page == "Genre Timelines":
    st.header("📅 Historical Color Strip")
    all_genres = sorted(list(set(df["Genres"].str.split("|").explode().str.strip().unique())))
    sel_genre = st.selectbox("Select Genre", all_genres)
    g_df = df[df["Genres"].str.contains(sel_genre, case=False, na=False)]

    for yr in sorted(g_df["Year"].unique(), reverse=True)[:30]:
        y_data = g_df[g_df["Year"] == yr]
        pal = get_representative_palette(y_data, count=5)
        c1, c2, c3 = st.columns([1, 2, 6])
        c1.write(f"**{yr}**")
        c2.caption(y_data["Art_Style"].mode()[0])
        with c3:
            html = '<div style="display: flex; height: 20px; border-radius: 4px; overflow: hidden; margin-bottom: 5px; border: 1px solid #333;">'
            for color in pal:
                html += f'<div style="background-color:{color}; flex:1;"></div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
