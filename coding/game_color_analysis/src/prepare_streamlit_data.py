import pandas as pd
import os

# Paths
RAW_CSV = "data/test_game_data.csv"
OUT_PARQUET = "data/game_summary.parquet"


def optimize_data():
    if not os.path.exists(RAW_CSV):
        print(f"Error: {RAW_CSV} not found.")
        return

    print("🚀 Loading raw data (this might take a moment)...")
    # low_memory=False prevents DtypeWarnings
    df = pd.read_csv(RAW_CSV, low_memory=False)

    # 1. Group by Game and Year to aggregate screenshots
    print("📊 Summarizing game palettes...")

    # Identify color columns (C1_R through C10_W)
    color_cols = [col for col in df.columns if col.startswith("C")]

    # We want to keep these identifying columns
    info_cols = ["Year", "Decade", "Genres", "Developers"]

    # Create the summary:
    # - Take the first occurrence of info (Year, Genres, etc.)
    # - Take the MEAN of all color values across the 5 screenshots
    agg_rules = {col: "first" for col in info_cols}
    for col in color_cols:
        agg_rules[col] = "mean"

    game_summary = df.groupby("Game").agg(agg_rules).reset_index()

    # 2. Cleanup: Ensure weights (W) sum to 1.0 properly after averaging
    weight_cols = [f"C{i}_W" for i in range(1, 11)]
    row_totals = game_summary[weight_cols].sum(axis=1)
    for col in weight_cols:
        game_summary[col] = game_summary[col] / row_totals

    # 3. Save as Parquet (Binary format is ~50x faster to load than CSV)
    print(f"💾 Saving to {OUT_PARQUET}...")
    game_summary.to_parquet(OUT_PARQUET, index=False)
    print("✅ Optimization complete! You can now run the Streamlit app.")


if __name__ == "__main__":
    optimize_data()
