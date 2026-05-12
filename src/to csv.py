import os
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")

OUTPUT_PARQUET = os.path.join(DATA_DIR, "final_game_data.parquet")

file_path = OUTPUT_PARQUET

if os.path.exists(file_path):
    print("Fixing URLs in Parquet file...")
    df = pd.read_parquet(file_path)

    def fix_url(url):
        url = url.strip()
        img_url = url.replace("t_thumb", "t_screenshot_big")
        if img_url.startswith("//"):
            return "https:" + img_url
        if not img_url.startswith("http"):
            return "https://" + img_url.lstrip("/")
        return img_url

    # Apply fix to the Screenshot column
    df["Screenshot"] = df["Screenshot"].apply(fix_url)

    # Save it back
    df.to_parquet(file_path, index=False)
    print("✅ Parquet file fixed! Your app should now load images correctly.")
else:
    print("❌ File not found.")
