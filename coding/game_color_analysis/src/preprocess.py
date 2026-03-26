import pandas as pd
import json
import helper_functions as helper
import os
import numpy as np


def fast_game_dna(group):
    """
    Highly optimized version of get_weighted_representative_palette
    Processes a whole game group at once using vectorized operations.
    """
    # 1. Gather all C1-C8 colors into one pool instantly
    # We reshape the dataframe to have R, G, B, W columns
    r_cols = [f"C{i}_R" for i in range(1, 9)]
    g_cols = [f"C{i}_G" for i in range(1, 9)]
    b_cols = [f"C{i}_B" for i in range(1, 9)]
    w_cols = [f"C{i}_W" for i in range(1, 9)]

    # Flatten the colors: This is 100x faster than a manual loop
    r = group[r_cols].values.flatten()
    g = group[g_cols].values.flatten()
    b = group[b_cols].values.flatten()
    w = group[w_cols].values.flatten()

    # Remove NaNs
    mask = ~np.isnan(r)
    r, g, b, w = r[mask], g[mask], b[mask], w[mask]

    if len(r) == 0:
        return ""

    # 2. Vectorized Bucketing
    r_b = (r // 20 * 20).clip(0, 255)
    g_b = (g // 20 * 20).clip(0, 255)
    b_b = (b // 20 * 20).clip(0, 255)
    sat = np.max([r, g, b], axis=0) - np.min([r, g, b], axis=0)

    # 3. Use a temp dataframe for the final aggregation (the only way to group colors)
    temp = pd.DataFrame({"R": r_b, "G": g_b, "B": b_b, "W": w, "sat": sat})
    grouped = (
        temp.groupby(["R", "G", "B"]).agg(total_w=("W", "sum"), max_s=("sat", "max")).reset_index()
    )

    # Ranking
    grouped["score"] = (grouped["total_w"] * 10) * (grouped["max_s"] + 5)
    top = grouped.nlargest(8, "score")

    # Normalize weights
    total_w = top["total_w"].sum()
    return "|".join(
        [
            f"#{int(row.R):02x}{int(row.G):02x}{int(row.B):02x},{row.total_w / total_w:.3f}"
            for row in top.itertuples()
        ]
    )


def run_preprocessing(csv_path="data/current_game_data.csv"):
    input_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), csv_path)
    print("🚀 Starting Pre-calculation Pipeline...")

    # 1. Load and Clean
    df = pd.read_csv(input_path)
    # Basic cleaning (ensure lowercase, numeric years, etc.)
    for col in ["Genres", "Themes", "Developers", "Game"]:
        df[col] = df[col].fillna("").astype(str).str.lower()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
    df["Decade"] = (df["Year"] // 10 * 10).astype(int).astype(str) + "s"

    # 2. Apply Taxonomy and Studio Normalization
    print("🏷️  Classifying Taxonomy...")
    df["Art_Style"] = df.apply(helper.classify_taxonomy, axis=1)
    df["Developers"] = df["Developers"].apply(helper.normalize_studio_name)

    # 3. Individual Game DNA (The "Weighted" Palettes)
    print("🧬  Generating Individual Game DNA...")
    unique_games = df["Game"].unique()
    dna_map = {}

    print(f"🧬 Processing {len(unique_games)} games...")
    print("🚀 Running Vectorized DNA Calculation...")
    dna_results = df.groupby("Game").apply(fast_game_dna)

    df["Precalc_DNA"] = df["Game"].map(dna_results)

    # 4. Global Summaries (Decades, Genres, Themes)
    # We store these in a JSON so the App doesn't have to filter thousands of rows
    summary_data = {"decades": {}, "genres": {}, "themes": {}}

    print("📊  Generating Global Overviews...")

    # Decade Palettes
    for dec in df["Year"].unique():
        if dec < 1970:
            continue
        dec_label = f"{(dec // 10) * 10}s"
        if dec_label not in summary_data["decades"]:
            subset = df[(df["Year"] >= (dec // 10) * 10) & (df["Year"] < (dec // 10) * 10 + 10)]
            summary_data["decades"][dec_label] = helper.get_representative_palette(subset, count=10)

    # Genre Palettes
    # all_genres = set(df["Genres"].str.split("|").explode())
    genre_df = df.copy()
    genre_df["Genres"] = genre_df["Genres"].str.split("|")
    genre_exploded = genre_df.explode("Genres")
    for gen, subset in genre_exploded.groupby("Genres"):
        if gen and len(subset) > 5:  # Only summarize genres with enough data
            summary_data["genres"][gen] = helper.get_representative_palette(subset, count=10)

    # 5. Save Outputs
    print("💾 Saving as optimized Parquet format...")
    out_parquet = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "processed_game_data.parquet"
    )
    df.to_parquet(out_parquet, engine="pyarrow", compression="snappy")
    # out_csv = os.path.join(
    #     os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/processed_game_data.csv"
    # )
    # df.to_csv(out_csv, index=False)
    out_json = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/summary_stats.json"
    )
    with open(out_json, "w") as f:
        json.dump(summary_data, f)

    print("✅ Done! App is now ready to run at high speed.")


if __name__ == "__main__":
    run_preprocessing()
