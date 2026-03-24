import os
import streamlit as st
import pandas as pd
import plotly.express as px
# import plotly.graph_objects as go

# Set page config for a wider layout
st.set_page_config(
    layout="wide", page_title="Evolution of Color and Art Styles in Video Game Design"
)
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


@st.cache_data
def load_data():
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/test_game_data.csv"
    )
    df = pd.read_csv(csv_path, low_memory=False)

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
    df["luminance"] = (0.2126 * df["C1_R"] + 0.7152 * df["C1_G"] + 0.0722 * df["C1_B"]) / 255.0

    # df["Decade"] = (df["Year"] // 10 * 10).astype(str) + "s"
    df["Decade"] = (df["Year"] // 10 * 10).astype(int).astype(str) + "s"

    return df[df["Year"] > 1950].copy(), unique_devs, top_studios_global


@st.cache_data
def load_summary():
    return pd.read_parquet(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/game_summary.parquet"
        )
    )


df, unique_devs_list, top_50_global = load_data()
df_summary = load_summary()


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


# --- 3. UI TABS ---
page = st.sidebar.radio(
    "Analysis Tabs",
    [
        "Market Trends (%)",
        "Color Archetypes",
        "Studio DNA",
        "Genre Timelines",
        "Aesthetic Mapping",
        "Game Search",
        "Game Search MIX",
        "game search 3.0",
        "Innovation & Impact",
    ],
)
all_genres = sorted(list(set(df["Genres"].str.split("|").explode().str.strip().unique())))

if page == "game search 3.0":
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
                    st.image(selected_game["Screenshot"], use_container_width=True)
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
                game_pal = get_representative_palette(game_subset, count=5)

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

    # Combined Search: Selectbox with unique names for accuracy
    unique_games = sorted(df["Game"].unique())
    selected_game_name = st.selectbox("Select or search a game:", unique_games)
    # selected_game = st.selectbox("Search for a game:", [""] + unique_games)

    if selected_game_name:
        # Filter for all rows belonging to this game
        game_rows = df[df["Game"] == selected_game_name]
        game_meta = df_summary[df_summary["Game"] == selected_game_name].iloc[0]

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
            game_pal = get_representative_palette(game_rows, count=10)

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
                st.image(row.Screenshot, use_container_width=True)
                single_img_data = game_rows[game_rows["Screenshot"] == row.Screenshot]
                screen_pal = get_representative_palette(single_img_data, count=5)

                mini_html = '<div style="display: flex; height: 12px; margin-top: -10px; border-radius: 0 0 5px 5px; overflow: hidden; border: 1px solid #333;">'
                for color in screen_pal:
                    mini_html += (
                        f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
                    )
                mini_html += "</div>"

                st.markdown(mini_html, unsafe_allow_html=True)
