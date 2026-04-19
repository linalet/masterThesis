"""Script made for preprocessing data to make loading faster"""

import os
import pandas as pd
import preprocess_helper as ph


def run_preprocessing(input_path="data/game_data.parquet"):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, input_path)

    df = pd.read_parquet(path)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    print(f"Detected columns: {df.columns.tolist()}")

    if "Is_NSFW" not in df.columns:
        df["Is_NSFW"] = False
    else:
        df["Is_NSFW"] = df["Is_NSFW"].fillna(False).astype(bool)

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
    df["Saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )
    decade_means = df.groupby("Decade")["Saturation"].mean()
    df["Decade_Avg_Saturation"] = df["Decade"].map(decade_means)

    print("🏷️ Applying Vectorized Taxonomy...")
    df["Art_Style"] = ph.classify_taxonomy(df)
    df["Is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")

    print("🖼 Saving screenshot URLs...")
    df = ph.finalize_screenshot_urls(df)

    search_cols = [
        "Unique_ID",
        "Game",
        "Year",
        "Decade",
        "Developers",
        "Screenshot",
        "Genres",
        "Themes",
        "Art_Style",
        "Is_classified",
        "Is_NSFW",
        "Saturation",
        "Decade_Avg_Saturation",
    ]
    df_search = df[search_cols]
    df_search.to_parquet(
        os.path.join(base_dir, "data/search_metadata.parquet"), engine="pyarrow", index=False
    )

    print("🎨 Calculating Color Metrics and Palettes...")
    if "Color_palette" in df.columns:
        df = df.drop(columns=["Color_palette"])
    color_palettes = df.groupby("Unique_ID").apply(ph.get_weighted_representative_palette)
    df["Color_palette"] = df["Unique_ID"].map(color_palettes)
    c_cols = [c for c in df.columns if c.startswith("C")]

    color_cols = [
        "Unique_ID",
        "Color_palette",
        "Screenshot",
        "Saturation",
    ] + c_cols
    df_colors = df[color_cols].copy()
    print(f"Detected columns: {df_colors.columns.tolist()}")
    df_colors = df_colors.loc[:, ~df_colors.columns.duplicated()]
    print(f"Detected columns: {df_colors.columns.tolist()}")
    df_colors.to_parquet(
        os.path.join(base_dir, "data/color_analytics.parquet"), engine="pyarrow", index=False
    )

    print("📊 Creating Aggregated Summaries...")
    genre_summary = ph.generate_timeline_summary(df, "Genres")
    genre_summary.to_parquet(
        os.path.join(base_dir, "data/genre_summaries.parquet"), engine="pyarrow", index=False
    )

    theme_summary = ph.generate_timeline_summary(df, "Themes")
    theme_summary.to_parquet(
        os.path.join(base_dir, "data/theme_summaries.parquet"), engine="pyarrow", index=False
    )

    print("✅ Timeline summaries saved to folder")
    print("📊 Pre-calculating Studio Profiles...")
    studio_summary = ph.generate_studio_summary(df)
    studio_summary.to_parquet(
        os.path.join(base_dir, "data/studio_summaries.parquet"), engine="pyarrow", index=False
    )

    print("✅ Preprocessing Complete.")


if __name__ == "__main__":
    print("Starting")
    run_preprocessing()
