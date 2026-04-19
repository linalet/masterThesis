import streamlit as st
import pandas as pd
import numpy as np
import os


def load_data(base_dir):
    path = os.path.join(base_dir, "data/search_metadata.parquet")
    df = pd.read_parquet(path, engine="pyarrow")

    df["Year"] = pd.to_numeric(df["Year"], downcast="integer")
    df["Decade"] = pd.to_numeric(df["Decade"], downcast="integer")

    df["Dev_List"] = df["Developers"].str.split("|")
    df["Genre_List"] = df["Genres"].str.split("|")
    df["Theme_List"] = df["Themes"].str.split("|")

    all_devs = df["Developers"].str.split("|").explode().str.strip()
    unique_devs = sorted(all_devs[all_devs != ""].unique().tolist())
    top_studios = all_devs[all_devs != "unknown"].value_counts().nlargest(50).index.tolist()

    return df, unique_devs, top_studios


@st.cache_data
def load_color_data(base_dir, unique_id=None):
    path = os.path.join(base_dir, "data/color_analytics.parquet")
    # If a unique_id is provided, we use 'filters' to only load 5 rows instead of 1 million
    if unique_id:
        return pd.read_parquet(path, filters=[("Unique_ID", "==", unique_id)])
    return pd.read_parquet(path)


def get_ranked_colors(df_row_or_group, count=5, filter_similarity=True):
    """
    The Universal Ranking Logic for the Thesis.
    Prioritizes saturated colors: (Weight * 10) * (Saturation + 5)
    """
    r_cols = [f"C{i}_R" for i in range(1, 9)]
    g_cols = [f"C{i}_G" for i in range(1, 9)]
    b_cols = [f"C{i}_B" for i in range(1, 9)]
    w_cols = [f"C{i}_W" for i in range(1, 9)]

    if isinstance(df_row_or_group, pd.DataFrame):
        r = df_row_or_group[r_cols].values.flatten()
        g = df_row_or_group[g_cols].values.flatten()
        b = df_row_or_group[b_cols].values.flatten()
        w = df_row_or_group[w_cols].values.flatten()
    else:
        r = np.array([getattr(df_row_or_group, c) for c in r_cols])
        g = np.array([getattr(df_row_or_group, c) for c in g_cols])
        b = np.array([getattr(df_row_or_group, c) for c in b_cols])
        w = np.array([getattr(df_row_or_group, c) for c in w_cols])

    mask = ~np.isnan(r) & (w > 0)
    r, g, b, w = r[mask], g[mask], b[mask], w[mask]

    if len(r) == 0:
        return []

    r_b, g_b, b_b = (r // 15 * 15), (g // 15 * 15), (b // 15 * 15)
    sat = np.max([r, g, b], axis=0) - np.min([r, g, b], axis=0)

    temp = pd.DataFrame({"R": r_b, "G": g_b, "B": b_b, "W": w, "S": sat})
    grouped = (
        temp.groupby(["R", "G", "B"]).agg(total_w=("W", "sum"), max_s=("S", "max")).reset_index()
    )

    grouped["score"] = (grouped["total_w"] * 10) * (grouped["max_s"] + 5)
    all_sorted = grouped.sort_values("score", ascending=False)

    if not filter_similarity:
        return all_sorted.head(count)

    final_selection = []
    for row in all_sorted.itertuples():
        if len(final_selection) >= count:
            break
        is_similar = False
        for chosen in final_selection:
            dist = (
                (row.R - chosen.R) ** 2 + (row.G - chosen.G) ** 2 + (row.B - chosen.B) ** 2
            ) ** 0.5
            if dist < 50:
                is_similar = True
                break
        if not is_similar:
            final_selection.append(row)

    return final_selection


def get_representative_palette(yr_data, count=10):
    top_colors = get_ranked_colors(yr_data, count=count)
    return [f"#{int(c.R):02x}{int(c.G):02x}{int(c.B):02x}" for c in top_colors]


def on_selectbox_change():
    if st.session_state.all_time_box != "Select...":
        st.session_state.all_search = ""


def on_text_change():
    if st.session_state.all_search.strip() != "":
        st.session_state.all_time_box = "Select..."


def on_selectbox_change_dec():
    if st.session_state.dec_box != "Select...":
        st.session_state.dec_search = ""


def on_text_change_dec():
    if st.session_state.dec_search.strip() != "":
        st.session_state.dec_box = "Select..."


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
