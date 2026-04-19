import pandas as pd
import os

# Path to your data
file_path = "data/game_data.parquet"

if os.path.exists(file_path):
    print("🛠️ Loading data to fix typo...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, file_path)
    df = pd.read_parquet(path)

    # Rename the column: { 'OldName': 'NewName' }
    df = df.rename(columns={"Persective": "Player_Perspective"})

    # Save it back to the same file
    df.to_parquet(file_path, index=False)
    print("✅ Fixed! 'Persective' is now 'Player_Perspective'.")
else:
    print("❌ File not found. Check your path!")
