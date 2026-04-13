"""Script made for preprocessing data to make loading faster"""

import os
import pandas as pd

# import helper_functions as helper
import preprocess_helper as ph


def run_preprocessing(input_path="data/octree_game_data.csv"):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), input_path)
    df = pd.read_csv(path, low_memory=False)
    if "is_nsfw" not in df.columns:
        df["is_nsfw"] = False
    else:
        df["is_nsfw"] = df["is_nsfw"].fillna(False).astype(bool)

    for col in ["Genres", "Themes", "Keywords", "Developers", "Game", "Player_Perspective"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
    df["Decade"] = (df["Year"] // 10 * 10).astype(int)
    df["Developers"] = df["Developers"].apply(ph.normalize_studio_name)
    df["Unique_ID"] = (
        df["Game"] + " (" + df["Year"].astype(str) + ") " + df["Developers"].str.split("|").str[0]
    )

    print("🏷️ Applying Vectorized Taxonomy...")
    df["Art_Style"] = ph.classify_taxonomy(df)

    print("🎨 Calculating Color Metrics...")
    df["saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )
    df["luminance"] = (0.2126 * df["C1_R"] + 0.7152 * df["C1_G"] + 0.0722 * df["C1_B"]) / 255.0

    print("🧬 Generating Game DNA...")
    dna_results = df.groupby("Unique_ID").apply(ph.get_weighted_representative_palette)
    df["Precalc_DNA"] = df["Unique_ID"].map(dna_results)

    df["is_classified"] = ~df["Art_Style"].str.startswith("Unclassified")
    print("💾 Saving to Parquet...")
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data/processed_game_data.parquet",
    )
    df.to_parquet(path, engine="pyarrow", index=True)
    print("✅ Preprocessing Complete.")


if __name__ == "__main__":
    run_preprocessing()
