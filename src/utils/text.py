"""Text processing utilities."""

import re
from typing import Set


def normalize_track_name(name: str) -> str:
    """
    Normalize a track name for comparison.
    
    Removes parentheses, remixes, versions, and special characters.
    Converts to lowercase.
    
    Args:
        name: Track name to normalize
    
    Returns:
        Normalized track name
    """
    # Remove content in parentheses/brackets
    name = re.sub(r"[\(\[].*?[\)\]]", "", name)
    name = name.replace("(", "").replace(")", "")
    
    # Remove remix/version indicators and everything after
    name = re.sub(r"\b(from|feat|ft|vs|remix|mix|version)\b.*", "", name, flags=re.IGNORECASE)
    
    # Remove special characters, keep only alphanumeric and spaces
    name = re.sub(r"[^\w\s]", " ", name)
    
    # Normalize whitespace and convert to lowercase
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name


def get_normalized_words(name: str) -> Set[str]:
    """
    Get set of words from normalized track name.
    
    Args:
        name: Track name
    
    Returns:
        Set of words from normalized name
    """
    normalized = normalize_track_name(name)
    return set(normalized.split())


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Sanitize a string for use as a filename.
    
    Removes invalid characters and limits length.
    
    Args:
        name: Original filename
        max_length: Maximum filename length
    
    Returns:
        Sanitized filename
    """
    # Remove invalid characters for filenames
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Limit length
    return name[:max_length]
