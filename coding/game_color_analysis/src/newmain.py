"""Main script to fetch game data and analyze color palettes from screenshots."""

import csv
import os
import pandas as pd
from PIL import Image

from igdb_api import download_image, query_igdb


START_YEAR = 1952
END_YEAR = 2026
SCREENSHOT_COUNT = 5  # possibly increase to 10
COLOR_COUNT = 10

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
csv_path = os.path.join(DATA_DIR, "test_game_data.csv")

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)

    # Check if the column exists
    if "Player Perspectives" in df.columns:
        # Hard delete the column
        df.drop(columns=["Player Perspectives"], inplace=True)

        # Save the cleaned file
        df.to_csv(csv_path, index=False)
        print("✅ Column 'Player Perspectives' has been deleted.")
    else:
        print("ℹ️ Column 'Player Perspectives' not found. It might already be gone.")
