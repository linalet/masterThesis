import pandas as pd
import re
import os

# Your updated map
studio_map = {
    "nintendo": [],
    "microsoft": [],
    "ubisoft": ["ubi soft", "ubi studios uk", "ubi pictures"],
    "sega": ["sega am", "sega wow", "sega technical institute", "sonic team"],
    "capcom": ["capcom production", "capcom development"],
    "konami": ["konami computer entertainment", "konami tokyo", "konami osaka"],
    "atari": ["atari games", "atari corporation", "atari interactive"],
    "ea": ["electronic arts", "ea sports", "ea canada"],
    "acclaim": [],
    "activision": [],
    "aeria games": [],
    "lucasarts": ["lucas arts"],
    "bandai namco": ["bandai", "namco"],
    "rockstar games": [
        "rockstar leeds",
        "rockstar north",
        "rockstar london",
        "rockstar toronto",
        "rockstar san diego",
        "rockstar vancouver",
        "rockstar new england",
    ],
    "thq": ["thq digital studios uk", "thq san diego", "thq studio australia", "thq studio oz"],
    "sony": [
        "sony xdev",
        "sony imagesoft",
        "sony pictures games",
        "sony pictures mobile",
        "sony pictures studios",
        "sony music entertainment",
        "sony online entertainment",
        "sony computer entertainment",
        "aony interactive entertainment",
        "sony music entertainment japan",
        "sony interactive studios america",
        "sony comupter entertainment japan",
        "sony comupter entertainment europe",
        "sony comupter entertainment america",
        "sony comupter entertainment of america",
        "sony pictures television uk rights limited",
    ],
    "tencent": ["tencent aurora studios"],
    "xbox game studios": ["xbox live production"],
    "disney": [
        "disney games",
        "disney mobile",
        "disney online",
        "disney canada inc.",
        "disney interactive",
        "disney imagineering",
        "disney interactive studios",
        "disney interactive victoria",
        "disney interactive studios beijing",
        "the walt disney company",
        "walt disney animation studios",
        "walt disney computer software",
    ],
    "mihoyo": ["hoyoverse", "cognosphere"],
    "playrix": ["lplayrix llc", "playrix entertainment"],
}


def normalize_studio_name(dev_string):
    parts = [p.strip() for p in dev_string.split("|")]
    cleaned_parts = []
    for part in parts:
        found_parent = False
        for parent, aliases in studio_map.items():
            if parent in part or any(alias in part for alias in aliases):
                cleaned_parts.append(parent)
                found_parent = True
                break
        if not found_parent:
            cleaned_parts.append(part)
    return "|".join(sorted(list(set(cleaned_parts))))


def fix_csv_ids(file_path="data/manual_classification.csv"):
    if not os.path.exists(file_path):
        print("CSV not found.")
        return

    df = pd.read_csv(file_path)
    original_count = len(df)

    def update_id(unique_id):
        # Regex to find content inside the last set of square brackets
        # Input: "Mario (2008) [nintendo|smart bomb interactive]"
        match = re.search(r"(.*)\[(.*)\]$", unique_id)
        if match:
            base_info = match.group(1)  # "Mario (2008) "
            studios = match.group(2)  # "nintendo|smart bomb interactive"

            normalized = normalize_studio_name(studios)
            return f"{base_info}[{normalized}]"
        return unique_id

    print("🔄 Normalizing IDs in CSV...")
    df["Unique_ID"] = df["Unique_ID"].apply(update_id)

    # Optional: Remove duplicates if the normalization caused two IDs to become identical
    df = df.drop_duplicates(subset=["Unique_ID"], keep="first")

    df.to_csv("data/new_manual_classification.csv", index=False)
    print(f"✅ Done! Updated {len(df)} entries. (Removed {original_count - len(df)} duplicates).")


if __name__ == "__main__":
    fix_csv_ids()
