import os
import pandas as pd

studio_map = {
    "nintendo": [],
    "ubisoft": [
        "ubi soft",
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

    return "|".join(list(set(cleaned_parts)))


def get_weighted_representative_palette(group):
    from helper_functions import get_ranked_colors

    top_colors = get_ranked_colors(group, count=8)
    if not top_colors:
        return ""

    total_w = sum(c.total_w for c in top_colors)
    return "|".join(
        [
            f"#{int(c.R):02x}{int(c.G):02x}{int(c.B):02x},{c.total_w / total_w:.3f}"
            for c in top_colors
        ]
    )


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
        "Stylization: Cartoon"
    )
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[is_free & text.str.contains("pixel|8-bit|16-bit|voxel", na=False), "Art_Style"] = (
        "Stylization: Pixel Art"
    )
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("claymation|papercraft|stop-motion|felt", na=False),
        "Art_Style",
    ] = "Stylization: Material-Based"
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("watercolor|hand-painted|hand-drawn|sketch", na=False),
        "Art_Style",
    ] = "Stylization: Illustrative"

    # is_free = df["Art_Style"] == "Unclassified"
    # df.loc[is_free & text.str.contains("3d|3-d", na=False), "Art_Style"] = "Unclassified 3D"
    # is_free = df["Art_Style"] == "Unclassified"
    # df.loc[is_free & text.str.contains("2d|2-d", na=False), "Art_Style"] = "Unclassified 2D"
    is_free = df["Art_Style"] == "Unclassified"
    df["is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")

    return df["Art_Style"]
