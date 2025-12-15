from colorthief import ColorThief
from sklearn.cluster import KMeans
import numpy as np

def extract_palette(image_path, color_count = 10):
    """Get dominant colors using ColorThief."""
    palette = []
    thief = ColorThief(image_path)
    palette = thief.get_palette(color_count = color_count)
    return palette
    
def cluster_palette(palette, n_clusters = 5):
    """Cluster colors in the palette using KMeans."""
    if not palette:
        return []
    
    arr = np.array(palette)
    kmeans = KMeans(n_clusters = min(n_clusters, len(arr)), random_state = 42)
    kmeans.fit(arr)
    clustered_colors = [tuple(map(int, c)) for c in kmeans.cluster_centers_]
    return clustered_colors
    
