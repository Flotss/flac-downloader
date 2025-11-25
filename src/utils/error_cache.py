"""Error cache management for failed track downloads."""

import json
import os
import time
from typing import Dict, Set

from src.config import settings
from src.core.logging import get_logger

logger = get_logger()


class ErrorCache:
    """Cache for tracking failed track downloads to avoid retrying them."""
    
    def __init__(self, cache_file: str = None):
        """
        Initialize error cache.
        
        Args:
            cache_file: Path to cache file (uses default if not provided)
        """
        self.cache_file = cache_file or os.path.join(settings.DATA_DIR, "error_cache.json")
        self.errors: Dict[str, Dict] = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Dict]:
        """
        Load error cache from file.
        
        Returns:
            Dictionary of cached errors
        """
        if not os.path.exists(self.cache_file):
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                logger.debug(f"📋 Error cache loaded: {len(cache)} entries")
                return cache
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"⚠️ Error cache corrupted, starting fresh")
            return {}
    
    def _save_cache(self) -> None:
        """Save error cache to file."""
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, indent=2, ensure_ascii=False)
                logger.debug(f"💾 Error cache saved: {len(self.errors)} entries")
        except Exception as e:
            logger.warning(f"⚠️ Could not save error cache: {e}")
    
    def _normalize_track_key(self, title: str, artist: str) -> str:
        """
        Create normalized cache key from track info.
        Normalise la casse, supprime les espaces en trop et remplace tous les espaces multiples par un seul.
        """
        import re
        def norm(s):
            # Enlève les espaces en début/fin, remplace les espaces multiples par un seul, met en minuscule
            return re.sub(r"\s+", " ", s.strip().lower())
        key = f"{norm(title)}|{norm(artist)}"
        return key
    
    def add_error(self, title: str, artist: str, error_reason: str) -> None:
        """
        Add a failed track to the error cache.
        
        Args:
            title: Track title
            artist: Artist name
            error_reason: Reason for failure
        """
        key = self._normalize_track_key(title, artist)
        
        self.errors[key] = {
            "title": title,
            "artist": artist,
            "error": error_reason,
            "timestamp": time.time(),
            "attempts": self.errors.get(key, {}).get("attempts", 0) + 1
        }
        
        logger.debug(f"❌ Error cached: {title[:30]} - {artist[:15]} ({error_reason[:30]})")
        self._save_cache()
    
    def is_failed(self, title: str, artist: str) -> bool:
        """
        Check if a track has previously failed.
        
        Args:
            title: Track title
            artist: Artist name
        
        Returns:
            True if track is in error cache
        """
        key = self._normalize_track_key(title, artist)
        return key in self.errors
    
    def get_error_reason(self, title: str, artist: str) -> str:
        """
        Get the error reason for a failed track.
        
        Args:
            title: Track title
            artist: Artist name
        
        Returns:
            Error reason or empty string if not in cache
        """
        key = self._normalize_track_key(title, artist)
        if key in self.errors:
            return self.errors[key].get("error", "Unknown error")
        return ""
    
    def get_failed_tracks(self) -> list:
        """
        Get all failed tracks from cache.
        
        Returns:
            List of failed track information
        """
        return list(self.errors.values())
    
    def get_failed_count(self) -> int:
        """
        Get total number of failed tracks in cache.
        
        Returns:
            Count of cached errors
        """
        return len(self.errors)
    
    def get_failed_count_by_reason(self) -> Dict[str, int]:
        """
        Get count of failures grouped by reason.
        
        Returns:
            Dictionary of error reasons and their counts
        """
        reasons = {}
        for error_info in self.errors.values():
            reason = error_info.get("error", "Unknown")
            reasons[reason] = reasons.get(reason, 0) + 1
        return reasons
    
    def clear_error(self, title: str, artist: str) -> bool:
        """
        Remove a track from error cache (e.g., after successful retry).
        
        Args:
            title: Track title
            artist: Artist name
        
        Returns:
            True if track was in cache and removed
        """
        key = self._normalize_track_key(title, artist)
        if key in self.errors:
            del self.errors[key]
            logger.debug(f"✅ Cleared error cache for: {title[:30]} - {artist[:15]}")
            self._save_cache()
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all cached errors."""
        count = len(self.errors)
        self.errors = {}
        self._save_cache()
        logger.info(f"🗑️ Error cache cleared ({count} entries removed)")
    
    def print_summary(self) -> None:
        """Print summary of cached errors."""
        if not self.errors:
            logger.info("✅ No cached errors")
            return
        
        logger.info("📊 CACHED ERRORS SUMMARY")
        logger.info(f"   Total failed: {len(self.errors)}")
        
        reasons = self.get_failed_count_by_reason()
        logger.info("   By reason:")
        for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"      • {reason}: {count}")
        
        # Show most recent failures
        sorted_errors = sorted(
            self.errors.values(),
            key=lambda x: x.get("timestamp", 0),
            reverse=True
        )[:5]
        
        if sorted_errors:
            logger.info("   Recent failures:")
            for error_info in sorted_errors:
                title = error_info.get("title", "Unknown")[:25]
                artist = error_info.get("artist", "Unknown")[:15]
                reason = error_info.get("error", "Unknown")[:30]
                logger.info(f"      • {title} - {artist} ({reason})")


# Global error cache instance
_error_cache: ErrorCache = None


def get_error_cache() -> ErrorCache:
    """Get or create the global error cache instance."""
    global _error_cache
    if _error_cache is None:
        _error_cache = ErrorCache()
    return _error_cache
