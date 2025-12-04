from colorthief import ColorThief
from sklearn.cluster import KMeans
import numpy as np

def extract_palette(image_path, color_count=10):
    """Extract dominant colors from an image using ColorThief."""
    try:
        ct = ColorThief(image_path)
        return ct.get_palette(color_count=color_count)
    except Exception as e:
        print(f"[ERROR] Palette extraction failed for {image_path}: {e}")
        return []

def cluster_palette(palette, n_clusters=5):
    """Optional: reduce a palette to fewer clusters using k-means."""
    if not palette:
        return []
    try:
        X = np.array(palette)
        kmeans = KMeans(n_clusters=min(n_clusters, len(X)), random_state=42)
        kmeans.fit(X)
        clustered_colors = [tuple(map(int, c)) for c in kmeans.cluster_centers_]
        return clustered_colors
    except Exception as e:
        print(f"[ERROR] Palette clustering failed: {e}")
        return palette
