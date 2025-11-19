import sqlite3
import os
from .config import DATABASE_PATH

def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute(""" 
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY,
        igdb_id INTEGER UNIQUE,
        name TEXT,
        release_year INTEGER,
        engine TEXT,
        genres TEXT,
        themes TEXT
    )
    """)

    c.execute(""" 
    CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY,
        game_id INTEGER,
        url TEXT,
        local_path TEXT
    )
    """)

    c.execute(""" 
    CREATE TABLE IF NOT EXISTS color_palettes (
        screenshot_id INTEGER,
        palette TEXT
    )
    """)

    conn.commit()
    conn.close()

def insert_game(conn, game_tuple):
    conn.execute(""" 
        INSERT OR IGNORE INTO games
        (igdb_id, name, release_year, engine, genres, themes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, game_tuple)

def insert_screenshot(conn, game_id, url, local_path):
    conn.execute(""" 
        INSERT INTO screenshots (game_id, url, local_path)
        VALUES (?, ?, ?)
    """, (game_id, url, local_path))
