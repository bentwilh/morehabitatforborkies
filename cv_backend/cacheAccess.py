import os
import math
from pathlib import Path
from PIL import Image
import numpy as np

class CacheAccess:
    def __init__(self, cache_dir='./cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)  # Ensure cache directory exists

    def get(self, lat_index, long_index, year, month):
        # Construct the directory path for the given indices
        index_dir = self.cache_dir / f"{lat_index}_{long_index}"
        if index_dir.exists():
            # Scan the directory for any files
            for file in index_dir.iterdir():
                if file.is_file():
                    # Return the first file found; this can be adjusted to select based on year and month
                    return str(file)
        return None


