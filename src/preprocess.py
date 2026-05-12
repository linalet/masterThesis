"""
Data processing converts data into summary files for the Streamlit app.
"""

import os
import pandas as pd
import preprocess_helper as ph
import helper_functions as helper


def run_preprocessing(input_path="data/final_game_data.parquet"):
    """Main preprocessing function to clean data, apply taxonomy, and generate summary files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, input_path)

    df = pd.read_parquet(path)

    # normalize and downcast data
    if "Is_NSFW" not in df.columns:
        df["Is_NSFW"] = False
    else:
        df["Is_NSFW"] = df["Is_NSFW"].fillna(False).astype(bool)

    for col in ["Genres", "Themes", "Keywords", "Player_Perspective"]:
        df[col] = df[col].fillna("").astype(str).str.lower()
    for col in ["Developers", "Game"]:
        df[col] = df[col].fillna("").astype(str)

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype("int16")
    df["Decade"] = pd.to_numeric(df["Decade"], errors="coerce").fillna(0).astype("int16")

    df["Developers"] = df["Developers"].apply(ph.normalize_studio_name)

    df["Unique_ID"] = (
        df["Game"].str.lower()
        + " ("
        + df["Year"].astype(str)
        + ") ["
        + df["Developers"]
        .str.lower()
        .str.split("|")
        .apply(
            lambda x: (
                sorted([i for i in x if i.strip()])[0]
                if x and any(i.strip() for i in x)
                else "Unknown"
            )
        )
        + "]"
    ).str.strip()

    for i in range(1, 11):
        for channel in ["R", "G", "B"]:
            col = f"C{i}_{channel}"
            df[col] = df[col].fillna(0).astype("uint8")
        df[f"C{i}_W"] = df[f"C{i}_W"].astype("float32")

    print("Applying taxonomy...")
    df = ph.classify_taxonomy(df)

    print("Calculating saturation metrics...")
    df[["Saturation", "Sat_Variance"]] = ph.get_sat_metrics(df)

    print("Generating game palettes...")
    game_palettes = df.groupby("Unique_ID").apply(
        lambda x: "|".join(ph.get_weighted_representative_palette(x)), include_groups=False
    )
    df["Color_Palette"] = df["Unique_ID"].map(game_palettes)

    print("Creating summaries...")

    style_p, class_s = ph.generate_style_stats(df)
    style_p.to_parquet(os.path.join(base_dir, "data/summary_style_popularity.parquet"))
    class_s.to_parquet(os.path.join(base_dir, "data/summary_success_rate.parquet"))

    ph.generate_decade_style_summary(df).to_parquet(
        os.path.join(base_dir, "data/summary_decades.parquet")
    )

    ph.generate_timeline_summary(df, "Genres").to_parquet(
        os.path.join(base_dir, "data/summary_genres.parquet")
    )
    ph.generate_timeline_summary(df, "Themes").to_parquet(
        os.path.join(base_dir, "data/summary_themes.parquet")
    )

    ph.generate_studio_summary(df).to_parquet(
        os.path.join(base_dir, "data/summary_studios.parquet")
    )

    sample_df = ph.create_homepage_samples(df, helper.taxonomy_data.values())
    sample_df.to_parquet("data/homepage_samples.parquet")

    search_cols = [
        "Unique_ID",
        "Game",
        "Year",
        "Decade",
        "Developers",
        "Art_Style",
        "Genres",
        "Themes",
        "Screenshot",
        "Is_NSFW",
    ]
    df.drop_duplicates("Unique_ID")[search_cols].to_parquet(
        os.path.join(base_dir, "data/search_metadata.parquet")
    )

    color_headers = []
    for i in range(1, 11):
        color_headers.extend([f"C{i}_R", f"C{i}_G", f"C{i}_B", f"C{i}_W"])
    keepers = [
        "Unique_ID",
        "Screenshot",
    ] + color_headers
    df_optimized = df[keepers]
    df_optimized.to_parquet(os.path.join(base_dir, "data/screenshot_colors.parquet"))

    keepers = [
        "Unique_ID",
        "Color_Palette",
        "Saturation",
        "Sat_Variance",
    ]
    df_optimized = df[keepers]
    print("Saving color analytics file...")
    df_optimized.to_parquet(os.path.join(base_dir, "data/color_analytics.parquet"))

    print("Preprocessing complete.")


if __name__ == "__main__":
    run_preprocessing()
