import os

def ensure_dirs():
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/screenshots', exist_ok=True)
