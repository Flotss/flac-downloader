"""Main downloader orchestration logic."""

import os
import time
from typing import Tuple

from src.config import settings
from src.core.logging import get_logger
from src.core.models import StreamInfo
from src.services.tidal_api import TidalAPI
from src.services.metadata import MetadataManager
from src.utils import normalize_track_name, get_normalized_words, sanitize_filename, list_audio_files
from src.utils.error_cache import get_error_cache

logger = get_logger()


class Downloader:
    """Main downloader service orchestrating the download process."""
    
    def __init__(self, api: TidalAPI = None):
        """
        Initialize downloader.
        
        Args:
            api: TidalAPI instance (creates new if not provided)
        """
        self.api = api or TidalAPI()
        self.metadata_manager = MetadataManager()
    
    def is_track_downloaded(self, title: str, artist: str, existing_files: list) -> bool:
        """
        Check if a track is already downloaded.
        
        Compares normalized title and artist with existing filenames.
        
        Args:
            title: Track title
            artist: Artist name
            existing_files: List of existing filenames
        
        Returns:
            True if track is already downloaded
        """
        title_words = get_normalized_words(title)
        artist_words = get_normalized_words(artist)
        
        min_title_matches = min(2, len(title_words))
        min_artist_matches = 1
        
        for filename in existing_files:
            if not filename.lower().endswith(settings.VALID_AUDIO_EXTENSIONS):
                continue
            
            norm_file = normalize_track_name(filename)
            file_words = set(norm_file.split())
            
            title_matches = len(title_words & file_words)
            artist_matches = len(artist_words & file_words)
            
            if title_matches >= min_title_matches and artist_matches >= min_artist_matches:
                return True
        
        return False
    
    def is_in_error_cache(self, title: str, artist: str) -> bool:
        """
        Check if a track is in the error cache (without processing).
        
        Args:
            title: Track title
            artist: Artist name
        
        Returns:
            True if track is in error cache
        """
        error_cache = get_error_cache()
        return error_cache.is_failed(title, artist)
    
    def download_song(self, title: str, artist: str) -> Tuple[str, int]:
        """
        Download a single track.
        
        Attempts two strategies:
        1. Direct /song/ endpoint
        2. Fallback to search + stream
        
        Args:
            title: Track title
            artist: Artist name
        
        Returns:
            Tuple of (status, track_id)
            Status: 'Success', 'Failed (Song not found)', or 'Failed (Download error)'
        """
        search_query = f"{title} {artist}"
        track_id = 0
        
        logger.debug(f"   Search query: \"{search_query[:60]}...\"")
        
        # Strategy 1: Direct endpoint
        logger.debug(f"   📡 Method 1: Direct /song/ endpoint")
        stream_info = self.api.get_song_direct(search_query)
        
        # Strategy 2: Search + get stream separately
        if not stream_info:
            logger.debug(f"   📡 Method 2: Search + Stream separately")
            stream_info = self._search_and_match_track(title, artist)
        
        if not stream_info:
            # Return error without caching (let main.py cache after all retries)
            return ("Failed (Song not found)", 0)
        
        track_id = stream_info.track.id
        
        # Download the track
        safe_title = sanitize_filename(title)
        safe_artist = sanitize_filename(artist)
        filename = f"{safe_artist} - {safe_title}.flac"
        filepath = os.path.join(settings.DOWNLOAD_FOLDER, filename)
        
        logger.debug(f"   📁 File: {filename}")
        
        if self.api.download_track(stream_info.stream_url, filepath):
            # Download and add cover art
            cover_path = None
            if stream_info.track.cover_id:
                cover_filename = f".cover_{os.path.splitext(filename)[0]}.jpg"
                cover_filepath = os.path.join(settings.DOWNLOAD_FOLDER, cover_filename)
                
                if self.api.download_cover(stream_info.track.cover_id, cover_filepath):
                    cover_path = cover_filepath
                    logger.debug(f"   🖼️ Cover downloaded and embedded")
            
            # Add metadata with cover
            self.metadata_manager.add_track_metadata(
                filepath, 
                track_id, 
                title, 
                artist,
                album=stream_info.track.album,
                cover_path=cover_path
            )
            
            # Clean up temp cover file after embedding
            if cover_path and os.path.exists(cover_path):
                try:
                    os.remove(cover_path)
                    logger.debug(f"   🗑️ Temp cover file cleaned up")
                except Exception as e:
                    logger.debug(f"   ⚠️ Could not remove temp cover: {e}")
            
            return ("Success", track_id)
        
        # Track download failed (let main.py cache after all retries)
        return ("Failed (Download error)", track_id)
    
    def _search_and_match_track(self, title: str, artist: str) -> Tuple:
        """
        Search for track and find best match.
        
        Args:
            title: Track title
            artist: Artist name
        
        Returns:
            StreamInfo or None
        """
        search_query = f"{title} {artist}"
        tracks = self.api.search_tracks(search_query)
        
        if not tracks:
            logger.warning(f"   📭 No results for this search")
            return None
        
        # Find best matching track
        logger.debug(f"   🎯 Analyzing {len(tracks)} results to find best match...")
        best_match = None
        best_score = 0
        norm_title = normalize_track_name(title)
        norm_artist = normalize_track_name(artist)
        
        for track in tracks:
            track_title_norm = normalize_track_name(track.title)
            track_artist_norm = normalize_track_name(track.artist)
            
            title_words = get_normalized_words(title)
            artist_words = get_normalized_words(artist)
            track_title_words = set(track_title_norm.split())
            track_artist_words = set(track_artist_norm.split())
            
            title_match = len(title_words & track_title_words) / max(len(title_words), 1)
            artist_match = len(artist_words & track_artist_words) / max(len(artist_words), 1)
            score = title_match * 0.6 + artist_match * 0.4
            
            logger.debug(f"      Score {score:.2f}: {track.title[:25]} - {track.artist[:15]}")
            
            if score > best_score:
                best_score = score
                best_match = track
        
        if not best_match or best_score < 0.3:
            logger.warning(f"   ❌ No sufficient match (best score: {best_score:.2f})")
            return None
        
        logger.info(f"   🎯 Match found (score: {best_score:.2f}): {best_match.title[:30]} - {best_match.artist[:20]}")
        
        stream_info = self.api.get_track_stream(best_match.id)
        if not stream_info:
            logger.warning(f"   ❌ Cannot obtain stream for track ID {best_match.id}")
            return None
        
        return stream_info
