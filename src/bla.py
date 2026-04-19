import pandas as pd
import helper_functions as helper


def generate_style_stats(df):
    """Generates percentages for Art Style Popularity charts."""
    # Annual % of each style
    yearly_counts = df.groupby(["Year", "Art_Style"]).size().unstack(fill_value=0)
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
                summary.append(
                    {
                        "Item": item,
                        "Type": time_unit,
                        "Time": time_val,
                        "Palette": "|".join(palette),
                        "Top_Style": g["Art_Style"].mode()[0] if not g.empty else "Unknown",
                    }
                )
    return pd.DataFrame(summary)


def generate_studio_summary(df):
    """Generates DNA and Style distributions for top developers."""
    all_devs = df["Developers"].str.split("|").explode().str.strip()
    top_50 = all_devs[all_devs != "unknown"].value_counts().nlargest(50).index.tolist()

    rows = []
    for studio in top_50:
        s_df = df[df["Developers"].str.contains(studio, case=False, na=False, regex=False)]
        palette = helper.get_representative_palette(s_df, count=10)
        style_dist = s_df["Art_Style"].value_counts(normalize=True).to_dict()

        rows.append(
            {
                "Studio": studio,
                "Palette": "|".join(palette),
                "Style_Distribution": style_dist,
                "Game_Count": s_df["Unique_ID"].nunique(),
            }
        )
    return pd.DataFrame(rows)


def finalize_screenshot_urls(df):
    """Converts local IDs to full IGDB CDN links."""

    def to_url(img_id):
        if pd.isna(img_id) or img_id == "":
            return "https://via.placeholder.com/1280x720"
        return f"https://images.igdb.com/igdb/image/upload/t_screenshot_huge/{img_id}.jpg"

    df["Screenshot"] = df["Screenshot"].apply(to_url)
    return df
