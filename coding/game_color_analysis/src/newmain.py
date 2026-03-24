import streamlit as st
import pandas as pd
import plotly.express as px

# Set Page Config for a professional look
st.set_page_config(page_title="Game Color Analysis", layout="wide")


@st.cache_data
def load_data():
    """Loads the pre-optimized Parquet file."""
    try:
        df = pd.read_parquet("data/game_summary.parquet")
        return df
    except Exception as e:
        st.error(f"Could not load data. Did you run prepare_data.py? Error: {e}")
        return None


def draw_palette_bar(row, height=80):
    """Generates a clean HTML/CSS color bar for a game."""
    html = f'<div style="display: flex; height: {height}px; width: 100%; border-radius: 8px; overflow: hidden; border: 1px solid #333;">'
    for i in range(1, 11):
        r = row[f"C{i}_R"]
        g = row[f"C{i}_G"]
        b = row[f"C{i}_B"]
        w = row[f"C{i}_W"]
        if pd.notna(r) and w > 0:
            html += f'<div style="background-color: rgb({int(r)},{int(g)},{int(b)}); flex: {w};" title="Weight: {w:.1%}"></div>'
    html += "</div>"
    return html


# --- Main App Logic ---
df = load_data()

if df is not None:
    st.title("🎮 Game Color Aesthetic Analysis")

    # Sidebar Navigation
    menu = ["Era Trends", "Game Search", "Genre Mapping"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "Era Trends":
        st.header("📈 Color Evolution by Decade")
        # Example Plotly chart using the fast data
        avg_year = df.groupby("Year")[["C1_R", "C1_G", "C1_B"]].mean().reset_index()
        fig = px.line(
            avg_year,
            x="Year",
            y=["C1_R", "C1_G", "C1_B"],
            color_discrete_sequence=["red", "green", "blue"],
            title="Primary Color Channel Trends",
        )
        st.plotly_chart(fig, use_container_width=True)

    elif choice == "Game Search":
        st.header("🔍 Individual Game Palette")

        # UI Fragment: This ensures typing in the box doesn't reload the whole app
        @st.fragment
        def search_section():
            all_games = sorted(df["Game"].unique())
            selected_game = st.selectbox("Type a game name:", [""] + all_games)

            if selected_game:
                game_data = df[df["Game"] == selected_game].iloc[0]

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**Year:** {int(game_data.Year)}")
                    st.write(f"**Genres:** {game_data.Genres}")
                    st.write(f"**Studio:** {game_data.Developers}")

                with col2:
                    st.write("### Aggregate Palette (Avg of 5 Screenshots)")
                    st.markdown(draw_palette_bar(game_data), unsafe_allow_html=True)

        search_section()

    elif choice == "Genre Mapping":
        st.header("🎭 Genre Aesthetic Comparison")
        selected_genre = st.selectbox("Select Genre:", df["Genres"].unique())
        genre_df = df[df["Genres"] == selected_genre].sort_values("Year")

        st.write(f"Showing aesthetic migration for {selected_genre} over time:")
        for idx, row in genre_df.head(10).iterrows():
            st.write(f"**{row.Game} ({int(row.Year)})**")
            st.markdown(draw_palette_bar(row, height=40), unsafe_allow_html=True)
