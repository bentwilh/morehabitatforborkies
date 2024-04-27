import os
import math
from pathlib import Path
from PIL import Image
import numpy as np
from datetime import datetime


class CacheAccess:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)  # Ensure cache directory exists

    def get(self, lat_index, long_index, start_year, start_month, end_year, end_month):
        start_date = datetime(start_year, start_month, 1)
        end_date = datetime(end_year, end_month, 28)
        # Construct the directory path for the given indices
        index_dir = self.cache_dir / f"{lat_index}_{long_index}"
        files_in_date_range = []
        if index_dir.exists():
            # Scan the directory for files that in date range
            for file in index_dir.iterdir():
                if file.is_file():
                    split_list = file.name.split("_")
                    file_date = datetime(int(split_list[0]), int(split_list[1].split('.')[0]), 1)
                    if start_date <= file_date and file_date <= end_date:
                        files_in_date_range.append(str(file))
            # Return list of files that match month and year
            return files_in_date_range
        return []


