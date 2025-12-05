import os

# ==========================
# IGDB API credentials
# ==========================
CLIENT_ID = "6k1gmqbtqyihlzrqijshniy5fs3xis"
ACCESS_TOKEN = "tf6tmtwd8q8s6vuhrxyjir9wjxmv6k"

# ==========================
# Project paths
# ==========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCREENSHOT_DIR = os.path.join(DATA_DIR, "screenshots")
OUTPUT_CSV = os.path.join(DATA_DIR, "color_palettes.csv")

# ==========================
# Other settings
# ==========================
START_YEAR = 1978
END_YEAR = 2025
MAX_SCREENSHOTS_PER_GAME = 5    # possibly increase to 10
COLOR_COUNT = 10                # possibly increase to 20
BATCH_SIZE = 500             # IGDB max per request is 500