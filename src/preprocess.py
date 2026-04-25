"""
Final Preprocessing Script
Converts data into summary files for the Streamlit app.
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

    if "Is_NSFW" not in df.columns:
        df["Is_NSFW"] = False
    else:
        df["Is_NSFW"] = df["Is_NSFW"].fillna(False).astype(bool)

    for col in ["Genres", "Themes", "Keywords", "Developers", "Game", "Player_Perspective"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype("int16")
    # new main can use:
    # df["Decade"] = pd.to_numeric(df["Decade"], errors="coerce").fillna(0).astype("int16")
    df["Decade"] = (df["Year"] // 10 * 10).astype("int16")

    print("🧹 Normalizing Studios & Generating IDs...")
    df["Developers"] = df["Developers"].apply(ph.normalize_studio_name)

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
    ).str.strip()
    for i in range(1, 11):
        for chan in ["R", "G", "B"]:
            col = f"C{i}_{chan}"
            df[col] = df[col].fillna(0).astype("uint8")
        df[f"C{i}_W"] = df[f"C{i}_W"].astype("float32")

    print("🏷️ Applying Vectorized Taxonomy...")
    df = ph.classify_taxonomy(df)
    # df["Is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")

    print("🎨 Calculating Saturation (Thesis Metric)...")
    # df["saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
    #     axis=1
    # )
    sat_data = df.apply(ph.get_sat_metrics, axis=1)
    df["Saturation"] = sat_data["Saturation"]
    df["Sat_Variance"] = sat_data["Sat_Variance"]

    print("🧬 Generating Game DNA (Top 8 Colors per Game)...")
    game_palettes = df.groupby("Unique_ID").apply(
        lambda x: "|".join(ph.get_weighted_representative_palette(x)), include_groups=False
    )
    df["Color_palette"] = df["Unique_ID"].map(game_palettes)

    print("🖼 Formatting Screenshot URLs...")
    df = ph.finalize_screenshot_urls(df)

    print("📊 Exporting Aggregated Summaries...")

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
        "Is_NSFW",
    ]
    print("💾 Saving Metadata file...")
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
    print("💾 Saving Screenshot palette file...")
    df_optimized.to_parquet(os.path.join(base_dir, "data/screenshot_colors.parquet"))

    keep_cols = [
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
        "Saturation",
        "Sat_Variance",
        "Is_classified",
        "Is_NSFW",
    ]
    df_optimized = df[keep_cols]
    print("💾 Saving Master Color Analytics file...")
    df_optimized.to_parquet(os.path.join(base_dir, "data/color_analytics.parquet"))

    sample_df = ph.create_homepage_samples(
        pd.read_parquet("data/color_analytics.parquet"), helper.taxonomy_data.values()
    )
    sample_df = ph.create_homepage_samples(df_optimized, helper.taxonomy_data.values())
    sample_df.to_parquet("data/homepage_samples.parquet")
    print(f"Created homepage_samples.parquet with {len(sample_df)} rows.")

    # compression="brotli"?

    print("✅ Preprocessing Complete. The app is now ready to run at high speed.")


if __name__ == "__main__":
    run_preprocessing()
