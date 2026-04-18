"""Script made for preprocessing data to make loading faster"""

import os
import pandas as pd
import preprocess_helper as ph


def run_preprocessing(input_path="data/final_game_data.csv"):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, input_path)

    df = pd.read_csv(path, low_memory=False)

    if "Is_nsfw" not in df.columns:
        df["Is_nsfw"] = False
    else:
        df["Is_nsfw"] = df["Is_nsfw"].fillna(False).astype(bool)

    for col in ["Genres", "Themes", "Keywords", "Developers", "Game", "Player_Perspective"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
    df["Decade"] = (df["Year"] // 10 * 10).astype(int)
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
                if isinstance(x, list) and any(i.strip() for i in x)
                else "unknown"
            )
        )
        + "]"
    )

    print("🏷️ Applying Vectorized Taxonomy...")
    df["Art_Style"] = ph.classify_taxonomy(df)
    df["Is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")

    print("🖼 Saving screenshot URLs...")
    df = ph.finalize_screenshot_urls(df)

    search_cols = ["Unique_ID", "Game", "Year", "Decade", "Developers", 
                   "Genres", "Themes", "Art_Style", "Is_classified", "Is_nsfw", "Screenshot"]
    df_search = df[search_cols]
    df_search.to_parquet(os.path.join(base_dir, "data/search_metadata.parquet"))


    print("🎨 Calculating Color Metrics and Palettes...")
    df["Saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )
    # df["luminance"] = (0.2126 * df["C1_R"] + 0.7152 * df["C1_G"] + 0.0722 * df["C1_B"]) / 255.0
    color_palettes = df.groupby("Unique_ID").apply(ph.get_weighted_representative_palette)
    df["Color_palette"] = df["Unique_ID"].map(color_palettes)
    
    color_cols = ["Unique_ID", "Color_palette", "Saturation", "C1_R", "C1_G", "C1_B"] 
    df_colors = df[color_cols]
    df_colors.to_parquet(os.path.join(base_dir, "data/color_analytics.parquet"))

    print("📊 Creating Aggregated Summaries...")
    genre_summary = generate_timeline_summary(df, "Genres")
    genre_summary.to_parquet(os.path.join(base_dir, "data/genre_summaries.parquet"), engine="pyarrow")

    theme_summary = generate_timeline_summary(df, "Themes")
    theme_summary.to_parquet(os.path.join(base_dir, "data/theme_summaries.parquet"), engine="pyarrow")

    print("✅ Timeline summaries saved to data/")
    
    print("✅ Preprocessing Complete.")


if __name__ == "__main__":
    run_preprocessing()
