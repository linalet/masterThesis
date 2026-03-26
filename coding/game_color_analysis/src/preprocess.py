import pandas as pd
import os
import helper_functions as helper


def run_preprocessing(input_path="data/current_game_data.csv"):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), input_path)
    df = pd.read_csv(path, low_memory=False)

    # 1. Clean & Basic Stats
    for col in ["Genres", "Themes", "Keywords", "Developers", "Game", "Player_Perspective"]:
        df[col] = df[col].fillna("").astype(str).str.lower()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
    df["Decade"] = (df["Year"] // 10 * 10).astype(int).astype(str) + "s"

    # 2. Vectorized Color Math (Fast)
    print("🎨 Calculating Color Metrics...")
    df["saturation"] = df[["C1_R", "C1_G", "C1_B"]].max(axis=1) - df[["C1_R", "C1_G", "C1_B"]].min(
        axis=1
    )
    df["luminance"] = (0.2126 * df["C1_R"] + 0.7152 * df["C1_G"] + 0.0722 * df["C1_B"]) / 255.0

    # 3. Apply Thesis Logic (Taxonomy & Studio Normalization)
    print("🏷️  Applying Taxonomy & Studio Normalization...")
    df["Art_Style"] = df.apply(helper.classify_taxonomy, axis=1)
    df["Developers"] = df["Developers"].apply(helper.normalize_studio_name)

    # 4. Vectorized DNA Calculation (The logic we discussed for 360k games)
    print("🧬 Generating Game DNA...")
    dna_results = df.groupby("Game").apply(helper.fast_game_dna)
    df["Precalc_DNA"] = df["Game"].map(dna_results)
    # 5. Save as Parquet
    print("💾 Saving to Parquet...")
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data/processed_game_data.parquet",
    )
    df.to_parquet(path, engine="pyarrow")
    print("✅ Preprocessing Complete.")


if __name__ == "__main__":
    run_preprocessing()
