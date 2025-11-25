"""CSV logging utilities for failed downloads."""

import os
from typing import List, Dict, Any

import pandas as pd

from src.config import settings
from src.core.logging import get_logger

logger = get_logger()


def save_failed_downloads(failed_songs: List[Dict[str, Any]]) -> None:
    """
    Save list of failed downloads to CSV file.
    
    Args:
        failed_songs: List of failed download records
    """
    if not failed_songs:
        return
    
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    
    try:
        df = pd.DataFrame(failed_songs)
        df.to_csv(settings.CSV_LOG, index=False)
        logger.info(f"📝 Failed downloads saved to: {settings.CSV_LOG}")
    except Exception as e:
        logger.error(f"Failed to save CSV log: {e}")


def load_failed_downloads() -> List[Dict[str, Any]]:
    """
    Load previously failed downloads from CSV.
    
    Returns:
        List of failed download records
    """
    if not os.path.exists(settings.CSV_LOG):
        return []
    
    try:
        df = pd.read_csv(settings.CSV_LOG)
        return df.to_dict('records')
    except Exception as e:
        logger.warning(f"Failed to load CSV log: {e}")
        return []
