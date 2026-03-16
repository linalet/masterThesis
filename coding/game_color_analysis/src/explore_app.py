import os
import streamlit as st
import pandas as pd
import plotly.express as px


# --- 1. DATA LOADING & TAXONOMY ---
@st.cache_data
def load_data():
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/new_game_data.csv"
    )
    df = pd.read_csv(csv_path)

    for col in ["Genres", "Themes", "Keywords", "Developers", "Game"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)

    def classify_taxonomy(row):
        text = f"{row['Keywords']} {row['Themes']} {row['Genres']}"
        if any(w in text for w in ["pixel art", "8-bit", "16-bit", "retro", "sprite"]):
            return "Pixel Art"
        if any(w in text for w in ["photorealistic", "realistic", "realism", "pbr", "ray-tracing"]):
            return "Photorealism"
        if any(w in text for w in ["cel-shaded", "anime", "stylized", "cartoon"]):
            return "Stylized (3D)"
        if any(w in text for w in ["low-poly", "retro-3d", "ps1-style"]):
            return "Low-Poly / Retro 3D"
        if any(w in text for w in ["hand-drawn", "illustrated", "sketch", "painted"]):
            return "Illustrated 2D"
        if any(w in text for w in ["hidden object", "visual novel", "fmv"]):
            return "Static / Photo-Based"
        if any(w in text for w in ["minimalist", "abstract", "text-based", "vector"]):
            return "Minimalist / Abstract"
        if row["Year"] < 1980:
            return "Early Electronic"
        return "Hybrid / Misc"

    df["Art_Style"] = df.apply(classify_taxonomy, axis=1)
    return df[df["Year"] > 1950].copy()


df = load_data()


# --- 2. THE SATURATED PALETTE ENGINE ---
def get_vibrant_palette(yr_data, count=5):
    """Clusters bold colors and avoids the 'grey out' effect."""
    vibrant = yr_data[(yr_data["C1_R"] + yr_data["C1_G"] + yr_data["C1_B"]) > 180].copy()
    if vibrant.empty:
        return ["#444444", "#888888", "#cccccc"]

    for c in ["R", "G", "B"]:
        vibrant[f"{c}_B"] = (vibrant[f"C1_{c}"] // 50 * 50).clip(0, 255)

    top = vibrant.groupby(["R_B", "G_B", "B_B"]).size().nlargest(count).reset_index()
    return [f"#{int(r):02x}{int(g):02x}{int(b):02x}" for r, g, b in zip(top.R_B, top.G_B, top.B_B)]


# --- 3. UI TABS ---
page = st.sidebar.radio(
    "Analysis Tabs", ["Market Trends (%)", "Color Archetypes", "Studio DNA", "Genre Timelines"]
)

# --- TAB: COLOR ARCHETYPES ---
if page == "Color Archetypes":
    st.header("🎨 Palette Archetypes & Technological Milestones")

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
    for dec in [1970, 1980, 1990, 2000, 2010, 2020]:
        dec_df = df[(df["Year"] >= dec) & (df["Year"] < dec + 10)]
        if not dec_df.empty:
            pal = get_vibrant_palette(dec_df, count=10)

            c1, c2, c3 = st.columns([1, 2, 6])
            c1.write(f"### {dec}s")
            c2.info(milestones.get(dec, ""))

            with c3:
                html = '<div style="display: flex; height: 40px; border-radius: 8px; overflow: hidden; border: 1px solid #333; margin-bottom: 20px;">'
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
            "Select Decade for Samples", options=[1970, 1980, 1990, 2000, 2010, 2020]
        )
    with col_y:
        style_choice = st.selectbox(
            "Focus Area", ["Overall Industry"] + sorted(df["Art_Style"].unique().tolist())
        )

    f_df = df[(df["Year"] >= decade_sel) & (df["Year"] < decade_sel + 10)]
    if style_choice != "Overall Industry":
        f_df = f_df[f_df["Art_Style"] == style_choice]

    if not f_df.empty:
        palette = get_vibrant_palette(f_df, count=8)
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

    # Section 1: All-Time Giants
    st.subheader("🏆 All-Time Industry Giants")
    top_10_all = df["Developers"].value_counts().nlargest(10).index.tolist()
    col1, col2 = st.columns([1, 2])
    with col1:
        sel_all = st.selectbox("Major Studio", ["Select..."] + top_10_all, key="all_time_box")
        search_all = st.text_input("Or search name:", "", key="all_search")
        final_all = search_all if search_all else (sel_all if sel_all != "Select..." else None)

    if final_all:
        all_df = df[df["Developers"].str.contains(final_all, case=False, na=False)]
        with col2:
            st.write(f"**Palette Signature: {final_all.title()}**")
            p_all = get_vibrant_palette(all_df, count=5)
            pc = st.columns(5)
            for j, c in enumerate(p_all):
                pc[j].markdown(
                    f"<div style='background-color:{c}; height:40px; border-radius:4px;'></div>",
                    unsafe_allow_html=True,
                )
            st.plotly_chart(
                px.pie(all_df, names="Art_Style", hole=0.4, height=300), width="stretch"
            )

    st.markdown("---")

    # Section 2: Decade Leaders
    st.subheader("⏳ Decade-Specific Leaders")
    dec_sel_s = st.selectbox("Pick Decade", [1980, 1990, 2000, 2010, 2020])
    dec_df_full = df[(df["Year"] >= dec_sel_s) & (df["Year"] < dec_sel_s + 10)]
    top_10_dec = dec_df_full["Developers"].value_counts().nlargest(10).index.tolist()

    col3, col4 = st.columns([1, 2])
    with col3:
        sel_dec = st.selectbox(
            f"Top Studios of the {dec_sel_s}s", ["Select..."] + top_10_dec, key="dec_box"
        )
        search_dec = st.text_input("Or search decade studio:", "", key="dec_search")
        final_dec = search_dec if search_dec else (sel_dec if sel_dec != "Select..." else None)

    if final_dec:
        dec_dev_df = dec_df_full[
            dec_df_full["Developers"].str.contains(final_dec, case=False, na=False)
        ]
        with col4:
            st.write(f"**{final_dec.title()}'s Style in the {dec_sel_s}s**")
            p_dec = get_vibrant_palette(dec_dev_df, count=5)
            pdc = st.columns(5)
            for j, c in enumerate(p_dec):
                pdc[j].markdown(
                    f"<div style='background-color:{c}; height:40px; border-radius:4px;'></div>",
                    unsafe_allow_html=True,
                )
            st.plotly_chart(px.bar(dec_dev_df, x="Art_Style", height=300), width="stretch")

# --- TAB: GENRE TIMELINES ---
elif page == "Genre Timelines":
    st.header("📅 Historical Color Strip")
    all_genres = sorted(list(set(df["Genres"].str.split("|").explode().str.strip().unique())))
    sel_genre = st.selectbox("Select Genre", all_genres)
    g_df = df[df["Genres"].str.contains(sel_genre, case=False, na=False)]

    for yr in sorted(g_df["Year"].unique(), reverse=True)[:25]:
        y_data = g_df[g_df["Year"] == yr]
        pal = get_vibrant_palette(y_data, count=5)
        c1, c2, c3 = st.columns([1, 2, 6])
        c1.write(f"**{yr}**")
        c2.caption(y_data["Art_Style"].mode()[0])
        with c3:
            html = '<div style="display: flex; height: 18px; border-radius: 4px; overflow: hidden; margin-bottom: 5px; border: 1px solid #333;">'
            for color in pal:
                html += f'<div style="background-color:{color}; flex:1;"></div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
