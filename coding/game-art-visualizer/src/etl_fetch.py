# Note: run as module: python -m src.etl_fetch
import os
import requests
import sqlite3
from .igdb_client import IGDBClient
from .db import get_connection, init_db, insert_game, insert_screenshot
from .palette import extract_palette, save_palette
from .config import SCREENSHOT_DIR

def igdb_id_to_year(ts):
    # convert unix timestamp to year; IGDB gives seconds since epoch
    try:
        return int(ts / 31557600) + 1970
    except:
        return None

def run_etl(limit=200):
    igdb = IGDBClient()
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    query = """
    fields name, first_release_date, genres, themes, game_engines, screenshots.url;
    where first_release_date != null;
    limit %d;
    """ % limit

    games = igdb.request("games", query)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    for g in games:
        release_year = igdb_id_to_year(g.get("first_release_date")) if g.get("first_release_date") else None

        engine = None
        if g.get("game_engines"):
            engine = str(g.get("game_engines")[0])

        game_tuple = (
            g.get("id"),
            g.get("name"),
            release_year,
            engine,
            ",".join(map(str, g.get("genres", []))),
            ",".join(map(str, g.get("themes", [])))
        )

        insert_game(conn, game_tuple)

        # fetch screenshots
        for s in g.get("screenshots", [])[:2]:
            url = s.get("url")
            if not url:
                continue
            filename = f"{g.get('id')}_{os.path.basename(url)}"
            path = os.path.join(SCREENSHOT_DIR, filename)

            # download only if needed
            if not os.path.exists(path):
                img_url = "https:" + url.replace("t_thumb", "t_screenshot_big")
                r = requests.get(img_url)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(r.content)
                else:
                    continue

            insert_screenshot(conn, g.get("id"), url, path)

            # extract and save palette
            try:
                palette = extract_palette(path)
                # find screenshot id we just inserted
                cur.execute("SELECT id FROM screenshots WHERE local_path = ?", (path,))
                row = cur.fetchone()
                screenshot_id = row[0] if row else None
                if screenshot_id:
                    save_palette(conn, screenshot_id, palette)
            except Exception as e:
                print(f"Palette extraction failed for {path}: {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    run_etl()
