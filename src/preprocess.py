"""
Final Preprocessing Script
Converts raw 1M row data into optimized summary files for the Streamlit app.
"""

import os
import pandas as pd
import preprocess_helper as ph
import helper_functions as helper


def run_preprocessing(input_path="data/game_data.parquet"):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, input_path)

    print("📖 Loading raw data...")
    df = pd.read_parquet(path)

    # 1. Clean and Standardize
    if "Is_NSFW" not in df.columns:
        df["Is_NSFW"] = False
    else:
        df["Is_NSFW"] = df["Is_NSFW"].fillna(False).astype(bool)

    for col in ["Genres", "Themes", "Keywords", "Developers", "Game", "Player_Perspective"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
    df["Decade"] = (df["Year"] // 10 * 10).astype(int)

    print("🧹 Normalizing Studios & Generating IDs...")
    df["Developers"] = df["Developers"].apply(ph.normalize_studio_name)

    # Generate the Unique_ID: Game (Year) [First Developer]
    df["Unique_ID"] = (
        df["Game"]
        + " ("
        + df["Year"].astype(str)
        + ") ["
        + df["Developers"]
        .str.split("|")
        .apply(
            lambda x: (
                sorted([i for i in x if i.strip()])[0]
                if x and any(i.strip() for i in x)
                else "Unknown"
            )
        )
        + "]"
    )

    print("🏷️ Applying Vectorized Taxonomy...")
    df["Art_Style"] = ph.classify_taxonomy(df)
    df["Is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")

    print("🎨 Calculating Saturation (Thesis Metric)...")
    # Using C1 (Primary color) to determine the saturation metric for the whole screenshot
    df["saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )

    print("🧬 Generating Game DNA (Top 8 Colors per Game)...")
    # This groups 1M rows into 400k games. This is the most time-consuming part.
    game_palettes = df.groupby("Unique_ID").apply(
        lambda x: "|".join(helper.get_representative_palette(x, count=8))
    )
    df["Color_palette"] = df["Unique_ID"].map(game_palettes)

    print("🖼 Formatting Screenshot URLs...")
    df = ph.finalize_screenshot_urls(df)

    # --- SAVE SUMMARY FILES ---
    print("📊 Exporting Aggregated Summaries...")

    # Style Popularity & Classification Rates
    style_p, class_s = ph.generate_style_stats(df)
    style_p.to_parquet(os.path.join(base_dir, "data/summary_style_popularity.parquet"))
    class_s.to_parquet(os.path.join(base_dir, "data/summary_success_rate.parquet"))

    # Era Vibe Palettes
    ph.generate_decade_style_summary(df).to_parquet(
        os.path.join(base_dir, "data/summary_decades.parquet")
    )

    # Genre & Theme Timelines
    ph.generate_timeline_summary(df, "Genres").to_parquet(
        os.path.join(base_dir, "data/summary_genres.parquet")
    )
    ph.generate_timeline_summary(df, "Themes").to_parquet(
        os.path.join(base_dir, "data/summary_themes.parquet")
    )

    # Studio Profiles
    ph.generate_studio_summary(df).to_parquet(
        os.path.join(base_dir, "data/summary_studios.parquet")
    )

    print("🔍 Creating Search Metadata Index...")
    search_cols = [
        "Unique_ID",
        "Game",
        "Year",
        "Decade",
        "Developers",
        "Art_Style",
        "Genres",
        "Themes",
        "Color_palette",
        "Screenshot",
    ]
    df.drop_duplicates("Unique_ID")[search_cols].to_parquet(
        os.path.join(base_dir, "data/search_metadata.parquet")
    )

    print("💾 Saving Master Color Analytics file...")
    df.to_parquet(os.path.join(base_dir, "data/color_analytics.parquet"))

    print("✅ Preprocessing Complete. The app is now ready to run at high speed.")


if __name__ == "__main__":
    run_preprocessing()
