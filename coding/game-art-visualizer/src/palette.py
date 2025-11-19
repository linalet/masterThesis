import json
from colorthief import ColorThief

def extract_palette(image_path, color_count=6):
    ct = ColorThief(image_path)
    palette = ct.get_palette(color_count=color_count)
    return palette

def save_palette(conn, screenshot_id, palette):
    conn.execute(""" 
        INSERT INTO color_palettes (screenshot_id, palette)
        VALUES (?, ?)
    """, (screenshot_id, json.dumps(palette)))
