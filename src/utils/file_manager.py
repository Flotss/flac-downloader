"""File system operations and management."""

import os
from typing import List

from src.config import settings
from src.core.logging import get_logger

logger = get_logger()


def ensure_directory_exists(path: str) -> None:
    """
    Ensure a directory exists, create if necessary.
    
    Args:
        path: Directory path
    """
    os.makedirs(path, exist_ok=True)


def list_audio_files(directory: str) -> List[str]:
    """
    List all audio files in a directory.
    
    Args:
        directory: Path to directory
    
    Returns:
        List of filenames with valid audio extensions
    """
    if not os.path.isdir(directory):
        return []
    
    audio_files = []
    try:
        for filename in os.listdir(directory):
            if filename.lower().endswith(settings.VALID_AUDIO_EXTENSIONS):
                audio_files.append(filename)
    except Exception as e:
        logger.warning(f"Error listing audio files: {e}")
    
    return audio_files


def is_file_downloaded(filepath: str, min_size: int = 1024) -> bool:
    """
    Check if a file exists and has minimum size.
    
    Args:
        filepath: Path to file
        min_size: Minimum file size in bytes
    
    Returns:
        True if file exists and meets minimum size
    """
    return os.path.exists(filepath) and os.path.getsize(filepath) > min_size


def delete_file(filepath: str) -> bool:
    """
    Delete a file safely.
    
    Args:
        filepath: Path to file
    
    Returns:
        True if deletion succeeded
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        logger.warning(f"Failed to delete {filepath}: {e}")
    
    return False


def get_file_size_mb(filepath: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        filepath: Path to file
    
    Returns:
        File size in MB
    """
    return os.path.getsize(filepath) / 1024 / 1024
