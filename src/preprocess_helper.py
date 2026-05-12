"""Preprocessing helper functions for normalizing data, classifying art styles, generating color palettes, and creating summary files."""

import os
import pandas as pd
import numpy as np
import re

studio_map = {
    "Nintendo": [],
    "Microsoft": [],
    "Riot": ["riot games"],
    "Rovio": [],
    "Square Enix": [
        "square product development division 1",
        "square product development division 2",
        "square product development division 3",
        "square product development division 4",
        "square product development division 5",
        "square product development division 6",
        "square",
        "squaresoft",
        "enix",
        "enix corporatio",
        "square usa",
        "squaresoft usa",
    ],
    "Ubisoft": ["ubi soft", "ubi studios uk", "ubi pictures"],
    "Sega": [
        "sega am",
        "sega wow",
        "sega technical institute",
        "sonic team",
    ],
    "Capcom": [
        "capcom production",
        "capcom development",
    ],
    "Konami": [
        "konami computer entertainment",
        "konami tokyo",
        "konami osaka",
    ],
    "Atari": [
        "atari games",
        "atari corporation",
        "atari interactive",
    ],
    "EA": ["electronic arts", "ea sports", "ea canada", "ea digital illusions ce"],
    "Acclaim": [],
    "Activision": [],
    "Blizzard Entertainment": ["blizzard north"],
    "Aeria Games": [],
    "Lucasarts": ["lucas arts"],
    "Bandai Namco": ["bandai", "namco"],
    "Rockstar Games": [
        "rockstar leeds",
        "rockstar north",
        "rockstar london",
        "rockstar toronto",
        "rockstar san diego",
        "rockstar vancouver",
        "rockstar new england",
    ],
    "THQ": ["thq digital studios uk", "thq san diego", "thq studio australia", "thq studio oz"],
    "Sony": [
        "sony xdev",
        "sony imagesoft",
        "sony pictures games",
        "sony pictures mobile",
        "sony pictures studios",
        "sony music entertainment",
        "sony online entertainment",
        "sony computer entertainment",
        "sony interactive entertainment",
        "sony music entertainment japan",
        "sony interactive studios america",
        "sony computer entertainment japan",
        "sony computer entertainment europe",
        "sony computer entertainment america",
        "sony computer entertainment of america",
        "sony pictures television uk rights limited",
    ],
    "Tencent": ["tencent aurora studios"],
    "Xbox Game Studios": ["xbox live production"],
    "Disney": [
        "disney games",
        "disney mobile",
        "disney online",
        "disney canada inc.",
        "disney interactive",
        "disney imagineering",
        "disney interactive studios",
        "disney interactive victoria",
        "disney interactive studios beijing",
        "the walt disney company",
        "walt disney animation studios",
        "walt disney computer software",
    ],
    "Mihoyo": ["hoyoverse", "cognosphere"],
    "Playrix": ["lplayrix llc", "playrix entertainment"],
    "Hyper-Devbox Japan": ["hyperdevbox japan", "hyberdevbox japan"],
    "2K": [],
}


def normalize_studio_name(dev_string):
    """Normalizes studio names using the studio_map."""
    devs = [d.strip() for d in dev_string.split("|")]
    cleaned_devs = []

    for dev in devs:
        found_parent = False
        for parent, aliases in studio_map.items():
            all_matches = [parent] + aliases
            for match in all_matches:
                pattern = rf"\b{re.escape(match)}\b"
                if re.search(pattern, dev, re.IGNORECASE):
                    cleaned_devs.append(parent)
                    found_parent = True
            if found_parent:
                break
        if not found_parent:
            cleaned_devs.append(dev)
    if cleaned_devs == [""]:
        return "Unknown"
    unique_devs = sorted(list(set(cleaned_devs)))
    return "|".join(unique_devs) if unique_devs else "Unknown"


def manual_classification(main_df, classified_path="data/manual_classification.csv"):
    """Applies manual art style classifications from a CSV file."""
    try:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), classified_path
        )
        classified = pd.read_csv(path)

        classified["Unique_ID"] = classified["Unique_ID"].str.lower().str.strip()

        main_df["Unique_ID_lower"] = main_df["Unique_ID"].str.lower().str.strip()
        df = main_df.merge(
            classified,
            left_on="Unique_ID_lower",
            right_on="Unique_ID",
            how="left",
            suffixes=("", "_manual"),
        )

        mask = df["Manual_Art_Style"].notna()
        df.loc[mask, "Art_Style"] = df.loc[mask, "Manual_Art_Style"]

        df.loc[mask, "Is_classified"] = True
        df = df.drop(columns=["Unique_ID_lower", "Unique_ID_manual", "Manual_Art_Style"])

        print(f"Successfully applied {mask.sum()} manual overrides.")
        return df
    except FileNotFoundError:
        print("No manual classification file found.")
        return main_df


def classify_taxonomy(df):
    """Classifies games into art styles."""
    df["Art_Style"] = "Unclassified"
    # completely manual classification
    df = manual_classification(df)

    # manually assigned franchises
    name_search = df["Game"].str.lower().str.strip()
    df.loc[
        (df["Art_Style"] == "Unclassified")
        & name_search.str.contains(
            "the sims|assassin's creed|counter-strike|fallout|god of war|half-life|age of empires|dark souls|tom clancy|far cry|powerwash|little nightmares",
            na=False,
        ),
        "Art_Style",
    ] = "Realism: Stylized"
    df.loc[
        (df["Art_Style"] == "Unclassified")
        & name_search.str.contains(
            "call of duty|resident evil|kingdom come: deliverance|gran turismo|uncharted 4|ea sports|silent hill|Microsoft Flight Simulator|death stranding",
            na=False,
        ),
        "Art_Style",
    ] = "Realism: Photoreal"
    df.loc[
        (df["Art_Style"] == "Unclassified")
        & name_search.str.contains("minecraft|deltarune", na=False),
        "Art_Style",
    ] = "Stylization: Pixel Art"
    df.loc[
        (df["Art_Style"] == "Unclassified")
        & name_search.str.contains(
            "genshin impact|fortnite|overwatch|crash bandicoot|tekken|lego|league of legends|overcooked|super smash bros.",
            na=False,
        ),
        "Art_Style",
    ] = "Stylization: Cartoon"
    df.loc[
        (df["Art_Style"] == "Unclassified")
        & name_search.str.contains(
            "borderlands|the walking dead:|the wolf among us|batman: the telltale|cuphead", na=False
        ),
        "Art_Style",
    ] = "Stylization: Illustrative"
    df.loc[
        (df["Art_Style"] == "Unclassified")
        & (df["Year"] < 2006)
        & name_search.str.contains("spider-man", na=False),
        "Art_Style",
    ] = "Stylization: Pixel Art"
    df.loc[
        (df["Art_Style"] == "Unclassified")
        & (df["Year"] > 2016)
        & name_search.str.contains("spider-man", na=False),
        "Art_Style",
    ] = "Realism: Stylized"

    # early games override
    text = (
        df["Keywords"].fillna("") + " " + df["Themes"].fillna("") + " " + df["Genres"].fillna("")
    ).str.lower()
    persp = df["Player_Perspective"].str.lower()

    is_free = df["Art_Style"] == "Unclassified"
    early = (df["Year"] < 1970) & (df["Year"] > 0)
    df.loc[early & persp.str.contains("text", na=False), "Art_Style"] = "Abstraction: Symbolic"
    df.loc[early & ~persp.str.contains("text", na=False), "Art_Style"] = "Abstraction: Minimalist"

    # keyword classification
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("text-based|experimental|abstract|ascii", na=False),
        "Art_Style",
    ] = "Abstraction: Symbolic"
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("minimalism|minimalist|geometry", na=False),
        "Art_Style",
    ] = "Abstraction: Minimalist"

    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("watercolor|hand-painted|hand-drawn", na=False),
        "Art_Style",
    ] = "Stylization: Illustrative"
    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("claymation|paper aesthetic|stop motion", na=False),
        "Art_Style",
    ] = "Stylization: Material-Based"

    is_free = df["Art_Style"] == "Unclassified"
    df.loc[
        is_free & text.str.contains("photoreal|ray tracing|realistic|4k|realism", na=False),
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
    df.loc[
        is_free & text.str.contains("pixel|8-bit|16-bit|voxel|pixel graphics", na=False),
        "Art_Style",
    ] = "Stylization: Pixel Art"

    is_free = df["Art_Style"] == "Unclassified"
    df["Is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")

    return df


def get_ranked_colors(colors, count=5):
    """Palette ranking prioritizing saturated colors"""
    r_cols = [f"C{i}_R" for i in range(1, 11)]
    g_cols = [f"C{i}_G" for i in range(1, 11)]
    b_cols = [f"C{i}_B" for i in range(1, 11)]
    w_cols = [f"C{i}_W" for i in range(1, 11)]

    if isinstance(colors, pd.DataFrame):
        r = colors[r_cols].values.flatten()
        g = colors[g_cols].values.flatten()
        b = colors[b_cols].values.flatten()
        w = colors[w_cols].values.flatten()
    else:
        r = np.array([getattr(colors, c) for c in r_cols])
        g = np.array([getattr(colors, c) for c in g_cols])
        b = np.array([getattr(colors, c) for c in b_cols])
        w = np.array([getattr(colors, c) for c in w_cols])

    mask = ~np.isnan(r) & (w > 0)
    r, g, b, w = r[mask], g[mask], b[mask], w[mask]

    if len(r) == 0:
        return []

    # pool similar colors
    r_b, g_b, b_b = (r // 15 * 15), (g // 15 * 15), (b // 15 * 15)
    chroma = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)

    df_rgb = pd.DataFrame({"R": r_b, "G": g_b, "B": b_b, "W": w, "S": chroma})
    grouped = (
        df_rgb.groupby(["R", "G", "B"]).agg(total_w=("W", "sum"), max_s=("S", "max")).reset_index()
    )

    grouped["score"] = (grouped["total_w"] * 10) * (grouped["max_s"] + 5)
    all_sorted = grouped.sort_values("score", ascending=False)

    # euclid distance filter
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


def get_representative_palette(yr_data):
    """Create hex codes from RGB values of top ranked colors"""
    top_colors = get_ranked_colors(yr_data, count=10)
    return [f"#{int(c.R):02x}{int(c.G):02x}{int(c.B):02x}" for c in top_colors]


def get_weighted_representative_palette(colors):
    """Create hex codes from RGB values of top ranked colors, weighted by their importance."""

    top_colors = get_ranked_colors(colors, count=8)
    if not top_colors:
        return ""

    total_w = sum(c.total_w for c in top_colors)
    return [
        f"#{int(c.R):02x}{int(c.G):02x}{int(c.B):02x},{c.total_w / total_w:.3f}" for c in top_colors
    ]


def get_sat_metrics(df):
    """
    Calculates mean chroma and chroma variance for each row.
    Vectorized — operates on the full DataFrame at once.
    Returns a DataFrame with 'Saturation' and 'Sat_Variance' columns.
    """
    r_cols = [f"C{i}_R" for i in range(1, 11)]
    g_cols = [f"C{i}_G" for i in range(1, 11)]
    b_cols = [f"C{i}_B" for i in range(1, 11)]

    r = df[r_cols].values
    g = df[g_cols].values
    b = df[b_cols].values

    chroma = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    return pd.DataFrame(
        {
            "Saturation": chroma.mean(axis=1),
            "Sat_Variance": chroma.std(axis=1),
        },
        index=df.index,
    )


def generate_style_stats(df):
    """Generates percentages for Art Style Popularity charts."""
    # Annual % of each style
    classified_df = df[df["Is_classified"]].copy()
    yearly_counts = classified_df.groupby(["Year", "Art_Style"]).size().unstack(fill_value=0)
    yearly_perc = yearly_counts.div(yearly_counts.sum(axis=1), axis=0) * 100
    yearly_df = yearly_perc.reset_index().melt(id_vars="Year", value_name="Percentage")

    # Classification success rate per decade
    success = df.groupby("Decade")["Is_classified"].mean() * 100
    success_df = success.reset_index(name="Rate")
    overall_rate = df["Is_classified"].mean() * 100
    overall_row = pd.DataFrame([{"Decade": 3000, "Rate": overall_rate}])
    success_df = pd.concat([success_df, overall_row], ignore_index=True)

    return yearly_df, success_df


def generate_decade_style_summary(df):
    """Calculates the decade stats for overall and per art style."""
    results = []
    decade_stats = (
        df.groupby("Decade").agg({"Saturation": "mean", "Sat_Variance": "mean"}).to_dict("index")
    )
    # overall decade stats
    for dec, dec_group in df.groupby("Decade"):
        global_palette = get_representative_palette(dec_group)
        results.append(
            {
                "Decade": dec,
                "Art_Style": "Global",
                "Palette": "|".join(global_palette),
                "Count": dec_group["Unique_ID"].nunique(),
                "Decade_Avg_Sat": decade_stats[dec]["Saturation"],
                "Decade_Avg_Var": decade_stats[dec]["Sat_Variance"],
            }
        )
    # per-art style decade stats
    for (dec, style), colors in df.groupby(["Decade", "Art_Style"]):
        palette = get_representative_palette(colors)
        results.append(
            {
                "Decade": dec,
                "Art_Style": style,
                "Palette": "|".join(palette),
                "Count": colors["Unique_ID"].nunique(),
                "Decade_Avg_Sat": decade_stats[dec]["Saturation"],
                "Decade_Avg_Var": decade_stats[dec]["Sat_Variance"],
            }
        )
    return pd.DataFrame(results)


def generate_timeline_summary(df, column):
    """Calculates Year and Decade palettes for genres/themes."""
    items = df[column].str.split("|").explode().str.strip().unique()
    items = [i for i in items if i and i != "unknown"]

    summary = []
    for item in items:
        item_df = df[df[column].str.contains(item, case=False, na=False, regex=False)]
        for time_unit in ["Year", "Decade"]:
            for time_val, g in item_df.groupby(time_unit):
                palette = get_representative_palette(g)
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
                        "Count": g["Unique_ID"].nunique(),
                    }
                )
    return pd.DataFrame(summary)


def generate_studio_summary(df):
    """Generates palette and art style distributions for developer studios, calculates top 50 studios.
    Both is prepared overall and per decade."""
    color_cols = []
    for i in range(1, 11):
        for channel in ["R", "G", "B"]:
            color_cols.append(f"C{i}_{channel}")
        color_cols.append(f"C{i}_W")
    required_cols = ["Unique_ID", "Developers", "Art_Style", "Decade"] + color_cols
    available_cols = [c for c in required_cols if c in df.columns]
    new_df = df[available_cols].copy()

    # prepare studios df
    new_df["Dev_List"] = new_df["Developers"].str.split("|")
    exploded = new_df.explode("Dev_List")
    exploded["Dev_List"] = exploded["Dev_List"].str.strip()
    exploded = exploded[exploded["Dev_List"] != "Unknown"]

    top_50_global = exploded["Dev_List"].value_counts().nlargest(50).index.tolist()

    top_50_by_decade = {}
    for dec, d_group in exploded.groupby("Decade"):
        top_50_by_decade[int(dec)] = d_group["Dev_List"].value_counts().nlargest(50).index.tolist()

    rows = []
    # all-time stats per studio
    for studio, s_df in exploded.groupby("Dev_List"):
        palette = get_representative_palette(s_df)
        unclassified_count = s_df["Art_Style"].str.contains("Unclassified", na=False).sum()
        unclassified_pct = unclassified_count / len(s_df) if len(s_df) > 0 else 0
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
                "Unclassified_Pct": unclassified_pct,
                "Game_Count": s_df["Unique_ID"].nunique(),
                "Is_Major": studio in top_50_global,
            }
        )
        # per-decade stats per studio
        for dec, dec_group in s_df.groupby("Decade"):
            dec_total = len(dec_group)
            dec_unclassified = dec_group["Art_Style"].str.contains("Unclassified", na=False).sum()
            dec_unclass_pct = dec_unclassified / dec_total if dec_total > 0 else 0

            dec_palette = get_representative_palette(dec_group)
            dec_classified = dec_group[
                ~dec_group["Art_Style"].str.contains("Unclassified", na=False)
            ]
            dec_style_dist = (
                dec_classified["Art_Style"].value_counts(normalize=True).to_dict()
                if not dec_classified.empty
                else {"Unknown": 1.0}
            )
            is_top_50_dec = studio in top_50_by_decade.get(int(dec), [])

            rows.append(
                {
                    "Studio": studio,
                    "Decade": str(int(dec)),
                    "Palette": "|".join(dec_palette),
                    "Style_Distribution": dec_style_dist,
                    "Unclassified_Pct": dec_unclass_pct,
                    "Game_Count": dec_group["Unique_ID"].nunique(),
                    "Is_Major": is_top_50_dec,
                }
            )

    return pd.DataFrame(rows)


def create_homepage_samples(df, taxonomy):
    """Prepares a sample of games for the homepage."""
    sample_ids = []
    for branch in taxonomy:
        for style_info in branch.values():
            for game_ref in style_info["example_games"]:
                sample_ids.append(game_ref["id"].lower())
    special_cases = ["worse than death (2019) [benjamin rivers]"]
    sample_ids.extend(special_cases)

    df["id_lower"] = df["Unique_ID"].str.lower()
    sample_df = df[df["id_lower"].isin(sample_ids)].copy()

    sample_df.drop(columns=["id_lower"], inplace=True)
    return sample_df
