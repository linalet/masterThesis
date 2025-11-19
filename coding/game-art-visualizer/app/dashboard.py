import streamlit as st
import sqlite3
import pandas as pd
import json
import matplotlib.pyplot as plt

conn = sqlite3.connect("data/games.db")

st.set_page_config(layout="wide")
st.title("🎨 Game Art & Color Palette Explorer")

df_games = pd.read_sql_query("SELECT * FROM games", conn)
df_shots = pd.read_sql_query("SELECT * FROM screenshots", conn)
df_pal = pd.read_sql_query("SELECT * FROM color_palettes", conn)

st.sidebar.header("Filters")

min_year = int(df_games['release_year'].dropna().min()) if not df_games['release_year'].dropna().empty else 1980
max_year = int(df_games['release_year'].dropna().max()) if not df_games['release_year'].dropna().empty else 2025

year = st.sidebar.slider("Year Range", min_year, max_year, (min_year, max_year))
genre_input = st.sidebar.text_input("Genres (comma separated)")

filtered = df_games[
    (df_games["release_year"] >= year[0]) &
    (df_games["release_year"] <= year[1])
]

if genre_input.strip():
    genre_list = [g.strip() for g in genre_input.split(",")]
    mask = filtered["genres"].apply(lambda x: any(gg in str(x) for gg in genre_list))
    filtered = filtered[mask]

st.write("### Filtered Games")
st.dataframe(filtered[['igdb_id','name','release_year','engine','genres','themes']].reset_index(drop=True))

# Palette visualization
st.write("### Color Palettes (sample)")

cur = conn.cursor()
for _, row in filtered.head(20).iterrows():
    game_id = row["igdb_id"]

    cur.execute(""" 
        SELECT color_palettes.palette
        FROM color_palettes
        JOIN screenshots ON screenshots.id = color_palettes.screenshot_id
        WHERE screenshots.game_id = ?
        LIMIT 1
    """, (game_id,))
    result = cur.fetchone()

    if result:
        palette = json.loads(result[0])
        st.write(f"**{row['name']} ({row.get('release_year')})**")

        fig, ax = plt.subplots(figsize=(6, 1))
        for i, color in enumerate(palette):
            ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=[c/255 for c in color]))
        ax.set_xlim(0, len(palette))
        ax.set_ylim(0, 1)
        ax.axis('off')
        st.pyplot(fig)
