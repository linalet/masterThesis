import os
import numpy as np
import pandas as pd

studio_map = {
    "nintendo": [
        # "nintendo r&d",
        # "nintendo ead",
        # "nintendo entertainment",
        # "nintendo ird",
        # "nintendo tokyo",
    ],
    "ubisoft": [
        "ubi soft",
        # "ubisoft montreal",
        # "ubisoft toronto",
        # "ubisoft paris",
        # "ubisoft entertainment",
        # "ubisoft pune",
        # "ubisoft milan",
        # "ubisoft osaka",
        # "ubisoft sofia",
        # "ubisoft nagoya",
    ],
    "sega": [
        "sega am",
        "sega wow",
        "sega technical institute",
        "sonic team",
    ],
    "capcom": [
        "capcom production",
        "capcom development",
    ],
    "konami": [
        "konami computer entertainment",
        "konami tokyo",
        "konami osaka",
    ],
    "atari": [
        "atari games",
        "atari corporation",
        "atari interactive",
    ],
    "ea": ["electronic arts", "ea sports", "ea canada"],
    "acclaim": [],
    "activision": [],
    "aeria games": [],
    "lucasarts": ["lucas arts"],
}


def normalize_studio_name(dev_string):
    # Split pipe-connected studios first
    parts = [p.strip() for p in dev_string.split("|")]
    cleaned_parts = []

    for part in parts:
        found_parent = False
        for parent, aliases in studio_map.items():
            if parent in part or any(alias in part for alias in aliases):
                cleaned_parts.append(parent)
                found_parent = True
                break
        if not found_parent:
            cleaned_parts.append(part)

    # Return joined string to keep original data structure for pooling
    return "|".join(list(set(cleaned_parts)))


def get_weighted_representative_palette(group):

    # 1. Gather all C1-C8 colors into one pool instantly
    # We reshape the dataframe to have R, G, B, W columns
    r_cols = [f"C{i}_R" for i in range(1, 9)]
    g_cols = [f"C{i}_G" for i in range(1, 9)]
    b_cols = [f"C{i}_B" for i in range(1, 9)]
    w_cols = [f"C{i}_W" for i in range(1, 9)]

    # Flatten the colors: This is 100x faster than a manual loop
    r = group[r_cols].values.flatten()
    g = group[g_cols].values.flatten()
    b = group[b_cols].values.flatten()
    w = group[w_cols].values.flatten()

    # Remove NaNs
    mask = ~np.isnan(r)
    r, g, b, w = r[mask], g[mask], b[mask], w[mask]

    if len(r) == 0:
        return ""

    # 2. Vectorized Bucketing
    r_b = (r // 20 * 20).clip(0, 255)
    g_b = (g // 20 * 20).clip(0, 255)
    b_b = (b // 20 * 20).clip(0, 255)
    sat = np.max([r, g, b], axis=0) - np.min([r, g, b], axis=0)

    # 3. Use a temp dataframe for the final aggregation (the only way to group colors)
    temp = pd.DataFrame({"R": r_b, "G": g_b, "B": b_b, "W": w, "sat": sat})
    grouped = (
        temp.groupby(["R", "G", "B"]).agg(total_w=("W", "sum"), max_s=("sat", "max")).reset_index()
    )

    # Ranking
    grouped["score"] = (grouped["total_w"] * 10) * (grouped["max_s"] + 5)
    top = grouped.nlargest(8, "score")

    # Normalize weights
    total_w = top["total_w"].sum()
    return "|".join(
        [
            f"#{int(row.R):02x}{int(row.G):02x}{int(row.B):02x},{row.total_w / total_w:.3f}"
            for row in top.itertuples()
        ]
    )


def classify_taxonomy(df):
    df["Art_Style"] = "Unclassified"
    text = (df["Keywords"] + " " + df["Themes"] + " " + df["Genres"]).str.lower()
    persp = df["Player_Perspective"].str.lower()

    # Manual categorization to ensure some accurate data
    df = manual_classification(df)
    is_free = df["Art_Style"] == "Unclassified"

    early = (df["Year"] < 1970) & (df["Year"] > 0)
    df.loc[early & persp.str.contains("text", na=False), "Art_Style"] = "Abstraction: Symbolic"
    df.loc[early & ~persp.str.contains("text", na=False), "Art_Style"] = "Abstraction: Minimalist"

    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("text-based|experimental|psychedelic|ascii", na=False),
        "Art_Style",
    ] = "Abstraction: Symbolic"
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("silhouette|geometric|minimalist", na=False),
        "Art_Style",
    ] = "Abstraction: Minimalist"

    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("photoreal|ray-tracing|pbr|realistic|4k|realism", na=False),
        "Art_Style",
    ] = "Realism: Photoreal"

    is_free = df["Art_Style"] == "Unclassified"
    df.loc[is_free & text.str.contains("cinematic|atmospheric", na=False), "Art_Style"] = (
        "Realism: Stylized"
    )
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[is_free & text.str.contains("anime|manga|chibi|cartoon", na=False), "Art_Style"] = (
        "Stylization: Caricature"
    )
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[is_free & text.str.contains("pixel|8-bit|16-bit|voxel", na=False), "Art_Style"] = (
        "Stylization: Pixel Art"
    )
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free
        & text.str.contains("claymation|papercraft|puppet|stop-motion|felt|ballpoint", na=False),
        "Art_Style",
    ] = "Stylization: Material-Based"
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free
        & text.str.contains("watercolor|hand-painted|comic|cel-shade|hand-drawn|sketch", na=False),
        "Art_Style",
    ] = "Stylization: Illustrative"

    # Priority 3: Final Fallbacks
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[is_free & text.str.contains("3d|3-d", na=False), "Art_Style"] = "Unclassified 3D"
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[is_free & text.str.contains("2d|2-d", na=False), "Art_Style"] = "Unclassified 2D"
    is_free = df["Art_Style"] == "Unclassified"
    df["is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")

    # manual assignment for top gaames of each year
    # https://www.imdb.com/list/ls023816644/

    return df["Art_Style"]


# def classify_taxonomy(row):
#     text = f"{row['Keywords']} {row['Themes']} {row['Genres']}".lower()
#     perspective = str(row.get("Player_Perspective", "")).lower().strip()

#     # III. ABSTRACTION
#     if any(w in text for w in ["text-based", "experimental", "psychedelic", "ascii"]):
#         return "Abstraction: Symbolic"
#     if any(w in text for w in ["flat art", "silhouette", "geometric", "minimalist"]):
#         return "Abstraction: Minimalist"

#     # I. REALISM
#     if any(w in text for w in ["photoreal", "ray-tracing", "pbr", "realistic", "4k"]):
#         return "Realism: Photoreal"
#     if any(w in text for w in ["cinematic", "fantasy realism", "atmospheric"]):
#         return "Realism: Stylized"  # literally 0 games

#     # II. STYLIZATION
#     if any(
#         w in text
#         for w in ["watercolor", "hand-painted", "comic", "cel-shade", "hand-drawn", "sketch"]


#     # fallback
#     if row["Year"] < 1970:
#         if "text" in perspective:
#             return "Abstraction: Symbolic"
#         return "Abstraction: Minimalist"
#     if any(w in text for w in ["3d", "3-D"]):
#         return "Unclassified 3D"
#     if any(w in text for w in ["2d", "2-D"]):
#         return "Unclassified 2D"
#     return "Unclassified"#     ):
#         return "Stylization: Illustrative"
#     if any(w in text for w in ["anime", "manga", "chibi", "cartoon"]):
#         return "Stylization: Caricature"
#     if any(w in text for w in ["pixel", "8-bit", "16-bit", "voxel"]):
#         return "Stylization: Pixel Art"
#     if any(
#         w in text
#         for w in ["claymation", "papercraft", "puppet", "stop-motion", "felt", "ballpoint"]
#     ):
#         return "Stylization: Material-Based"


def manual_classification(main_df, classified_path="data/manual_classification.csv"):
    try:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), classified_path
        )
        classified = pd.read_csv(path)

        classified["Unique_ID"] = classified["Unique_ID"].str.lower()

        df = main_df.merge(classified, on="Unique_ID", how="left")

        mask = df["Manual_Art_Style"].notna()
        df.loc[mask, "Art_Style"] = df.loc[mask, "Manual_Art_Style"]

        # 3. Clean up the temp column and mark as classified
        df.loc[mask, "is_classified"] = True
        df = df.drop(columns=["Manual_Art_Style"])

        print(f"✅ Successfully applied {mask.sum()} manual overrides.")
        return df
    except FileNotFoundError:
        print("⚠️ No overrides file found, skipping manual labels.")
        return main_df
