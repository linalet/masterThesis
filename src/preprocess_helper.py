import os
import pandas as pd
import helper_functions as helper

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
    if cleaned_parts == [""]:
        return "unknown"

    return "|".join(list(set(cleaned_parts)))


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
        df.loc[mask, "Is_classified"] = True
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
    df["Is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")

    return df["Art_Style"]


def finalize_screenshot_urls(df):
    """
    Converts local screenshot filenames/paths into IGDB CDN URLs.
    Format: https://images.igdb.com/igdb/image/upload/t_screenshot_huge/{image_id}.jpg
    """

    def convert_to_url(path):
        if pd.isna(path) or path == "":
            return "https://via.placeholder.com/1280x720?text=No+Image"

        # Extract the filename (e.g., 'co1r98.jpg') from the path
        filename = os.path.basename(str(path))
        # Get the ID without the extension
        image_id = os.path.splitext(filename)[0]

        return f"https://images.igdb.com/igdb/image/upload/t_screenshot_huge/{image_id}.jpg"

    # Overwrite the Screenshot column with the web URL
    df["Screenshot"] = df["Screenshot"].apply(convert_to_url)
    return df


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


def generate_style_stats(df):
    """Generates percentages for Art Style Popularity charts."""
    # Annual % of each style
    classified_df = df[df["Is_classified"] == True].copy()
    yearly_counts = classified_df.groupby(["Year", "Art_Style"]).size().unstack(fill_value=0)
    yearly_perc = yearly_counts.div(yearly_counts.sum(axis=1), axis=0) * 100
    yearly_df = yearly_perc.reset_index().melt(id_vars="Year", value_name="Percentage")

    # Classification success rate per decade
    success = df.groupby("Decade")["Is_classified"].mean() * 100
    return yearly_df, success.reset_index(name="Rate")


def generate_decade_style_summary(df):
    """Calculates the 'Era Vibe' palette for every Decade + Art Style combo."""
    results = []
    # Calculate global decade saturation averages for Section 6 comparison
    decade_avgs = df.groupby("Decade")["saturation"].mean().to_dict()

    for dec, dec_group in df.groupby("Decade"):
        global_palette = helper.get_representative_palette(dec_group, count=10)
        results.append(
            {
                "Decade": dec,
                "Art_Style": "Global",
                "Palette": "|".join(global_palette),
                "Count": len(dec_group),
                "Decade_Avg_Sat": decade_avgs.get(dec, 0),
            }
        )

    for (dec, style), group in df.groupby(["Decade", "Art_Style"]):
        palette = helper.get_representative_palette(group, count=10)
        results.append(
            {
                "Decade": dec,
                "Art_Style": style,
                "Palette": "|".join(palette),
                "Count": len(group),
                "Decade_Avg_Sat": decade_avgs.get(dec, 0),
            }
        )
    return pd.DataFrame(results)


def generate_timeline_summary(df, column):
    """Pre-calculates Year and Decade palettes for Genres/Themes."""
    items = df[column].str.split("|").explode().str.strip().unique()
    items = [i for i in items if i and i != "unknown"]

    summary = []
    for item in items:
        item_df = df[df[column].str.contains(item, case=False, na=False, regex=False)]
        for time_unit in ["Year", "Decade"]:
            for time_val, g in item_df.groupby(time_unit):
                palette = helper.get_representative_palette(g, count=10)
                classified_styles = g[~g["Art_Style"].str.contains("Unclassified", na=False)]
                summary.append(
                    {
                        "Item": item,
                        "Type": time_unit,
                        "Time": time_val,
                        "Palette": "|".join(palette),
                        "Top_Style": classified_styles["Art_Style"].mode()[0]
                        if not classified_styles.empty
                        else "Unknown",
                        "Count": len(g),
                    }
                )
    return pd.DataFrame(summary)


def generate_studio_summary(df):
    """Generates DNA and Style distributions for ALL developers with Top 50 ranking flags."""

    # color_cols = [f"C{i}_{channel}" for i in range(1, 9) for channel in ["R", "G", "B"]]
    color_cols = []
    for i in range(1, 9):
        for channel in ["R", "G", "B", "W"]:
            color_cols.append(f"C{i}_{channel}")
    required_cols = ["Unique_ID", "Developers", "Art_Style", "Decade", "saturation"] + color_cols
    available_cols = [c for c in required_cols if c in df.columns]
    temp_df = df[available_cols].copy()

    temp_df["Dev_List"] = temp_df["Developers"].str.split("|")
    exploded = temp_df.explode("Dev_List")
    exploded["Dev_List"] = exploded["Dev_List"].str.strip()
    exploded = exploded[exploded["Dev_List"] != "unknown"]

    top_50_global = exploded["Dev_List"].value_counts().nlargest(50).index.tolist()

    top_50_by_decade = {}
    for dec, d_group in exploded.groupby("Decade"):
        top_50_by_decade[int(dec)] = d_group["Dev_List"].value_counts().nlargest(50).index.tolist()

    rows = []

    for studio, s_df in exploded.groupby("Dev_List"):
        palette = helper.get_representative_palette(s_df, count=10)
        classified = s_df[~s_df["Art_Style"].str.contains("Unclassified", na=False)]
        style_dist = (
            classified["Art_Style"].value_counts(normalize=True).to_dict()
            if not classified.empty
            else {"Unknown": 1.0}
        )

        rows.append(
            {
                "Studio": studio,
                "Decade": "All-Time",
                "Palette": "|".join(palette),
                "Style_Distribution": style_dist,
                "Game_Count": s_df["Unique_ID"].nunique(),
                "Is_Major": studio in top_50_global,
            }
        )
        for dec, dec_group in s_df.groupby("Decade"):
            dec_palette = helper.get_representative_palette(dec_group, count=10)
            dec_classified = dec_group[
                ~dec_group["Art_Style"].str.contains("Unclassified", na=False)
            ]
            dec_style_dist = (
                dec_classified["Art_Style"].value_counts(normalize=True).to_dict()
                if not dec_classified.empty
                else {"Unknown": 1.0}
            )
            is_major_this_decade = studio in top_50_by_decade.get(int(dec), [])

            rows.append(
                {
                    "Studio": studio,
                    "Decade": str(int(dec)),
                    "Palette": "|".join(dec_palette),
                    "Style_Distribution": dec_style_dist,
                    "Game_Count": dec_group["Unique_ID"].nunique(),
                    "Is_Major": is_major_this_decade,
                }
            )

    return pd.DataFrame(rows)
