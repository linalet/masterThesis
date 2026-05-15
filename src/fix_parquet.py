"""
fix_parquet.py
Run this once on your machine to fix dtypes and recompress final_game_data.parquet.
Requirements: pip install pyarrow pandas

Usage:
    python fix_parquet.py
"""

import pandas as pd
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
INPUT = os.path.join(DATA_DIR, "final_game_data.parquet")
# INPUT = "data/final_game_data.parquet"
OUTPUT = os.path.join(DATA_DIR, "final_game_data_fixed.parquet")

print(f"Reading {INPUT}...")
df = pd.read_parquet(INPUT, engine="pyarrow")

before_rows = len(df)
print(f"Rows: {before_rows:,}  |  Columns: {len(df.columns)}")
print(f"Input size: {os.path.getsize(INPUT) / 1e6:.1f} MB")

# ── 1. Remove duplicates ──────────────────────────────────────────────────────
dupes = df.duplicated(subset=["Screenshot"]).sum()
if dupes > 0:
    print(f"Dropping {dupes:,} duplicate screenshots...")
    df = df.drop_duplicates(subset=["Screenshot"])
    print(f"Rows after dedup: {len(df):,}")

# ── 2. Fix color channel dtypes ───────────────────────────────────────────────
# RGB values are 0-255 integers → uint8 (1 byte instead of 8)
# Weights are 0.0-1.0 floats → float32 (4 bytes instead of 8)
# Replace any NaN/None in RGB with 0 first
print("Recasting color column dtypes...")
for i in range(1, 11):
    for ch in ["R", "G", "B"]:
        col = f"C{i}_{ch}"
        df[col] = df[col].fillna(0).clip(0, 255).astype("uint8")
    w_col = f"C{i}_W"
    df[w_col] = df[w_col].fillna(0.0).astype("float32")

# ── 3. Fix other numeric columns ──────────────────────────────────────────────
df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype("int16")
df["Is_NSFW"] = df["Is_NSFW"].fillna(0).astype("uint8")
if "Decade" in df.columns:
    df["Decade"] = pd.to_numeric(df["Decade"], errors="coerce").fillna(0).astype("int16")

# ── 4. Fill empty strings ─────────────────────────────────────────────────────
for col in [
    "Game",
    "Developers",
    "Genres",
    "Themes",
    "Keywords",
    "Player_Perspective",
    "Screenshot",
]:
    if col in df.columns:
        df[col] = df[col].fillna("")

# ── 5. Write with pyarrow + zstd compression ──────────────────────────────────
# zstd gives ~30-40% better compression than the default snappy,
# and pyarrow writes a single row group (much more efficient than
# fastparquet's append mode which creates hundreds of small row groups)
print(f"Writing {OUTPUT} with zstd compression...")
df.to_parquet(
    OUTPUT,
    engine="pyarrow",
    compression="zstd",  # best compression ratio
    index=False,
)

out_size = os.path.getsize(OUTPUT) / 1e6
in_size = os.path.getsize(INPUT) / 1e6
print(f"\nDone.")
print(f"  Input:  {in_size:.1f} MB")
print(f"  Output: {out_size:.1f} MB")
print(f"  Reduction: {(1 - out_size / in_size) * 100:.0f}%")
print(f"\nVerifying output...")
df_check = pd.read_parquet(OUTPUT, engine="pyarrow")
print(f"  Rows: {len(df_check):,}  Columns: {len(df_check.columns)}")
print(f"  C1_R dtype: {df_check['C1_R'].dtype}  (should be uint8)")
print(f"  C1_W dtype: {df_check['C1_W'].dtype}  (should be float32)")
print(f"  Year dtype: {df_check['Year'].dtype}   (should be int16)")
print("\nAll good. You can now replace final_game_data.parquet with the fixed file.")
