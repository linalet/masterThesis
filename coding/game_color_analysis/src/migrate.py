import csv
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
input_path = os.path.join(DATA_DIR, "test_game_data.csv")
output_path = os.path.join(DATA_DIR, "test_game_data_FIXED.csv")

# Define the new 10-color header (50 columns total)
base_headers = [
    "Year",
    "Decade",
    "Game",
    "Screenshot",
    "Genres",
    "Themes",
    "Keywords",
    "Player Perspectives",
    "Developers",
    "Is_NSFW",
]
color_headers = []
for i in range(1, 11):
    color_headers.extend([f"C{i}_R", f"C{i}_G", f"C{i}_B", f"C{i}_W"])
new_header = base_headers + color_headers

print("Starting manual repair of the CSV...")

with open(input_path, mode="r", encoding="utf-8") as infile:
    reader = csv.reader(infile)
    # Skip the old header in the file
    original_header = next(reader)

    with open(output_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        # Write our clean, new 50-column header
        writer.writerow(new_header)

        line_count = 0
        for row in reader:
            # If the row is old (roughly 30 columns), pad it to 50
            if len(row) < 50:
                padding_needed = 50 - len(row)
                row.extend([None] * padding_needed)
            # If the row is somehow longer than 50, trim it
            elif len(row) > 50:
                row = row[:50]

            writer.writerow(row)
            line_count += 1

print(f"Repair complete! Processed {line_count} rows.")
print(f"Check your data folder for: test_game_data_FIXED.csv")
