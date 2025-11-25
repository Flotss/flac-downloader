"""Spotify API integration for playlist management."""

import json
import os
import time
from typing import List, Tuple

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from src.config import settings
from src.core.logging import get_logger

logger = get_logger()


class SpotifyService:
    """Service for Spotify API interactions."""
    
    def __init__(self):
        """Initialize Spotify client with credentials."""
        auth_manager = SpotifyClientCredentials(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET
        )
        self.client = spotipy.Spotify(auth_manager=auth_manager)
    
    def get_playlist_tracks(self, playlist_url: str) -> List[Tuple[str, str]]:
        """
        Fetch all tracks from a Spotify playlist.
        
        Uses caching to avoid repeated API calls (1 hour expiry).
        
        Args:
            playlist_url: Spotify playlist URL
        
        Returns:
            List of (title, artist) tuples
        """
        logger.info(f"🎧 Connecting to Spotify...")
        logger.debug(f"   Playlist URL: {playlist_url}")
        
        try:
            # Extract playlist ID
            playlist_id = playlist_url.split("/")[-1].split("?")[0]
            logger.debug(f"   Playlist ID: {playlist_id}")
            
            # Check cache
            if os.path.exists(settings.TMP_PLAYLIST_FILE):
                file_age = time.time() - os.path.getmtime(settings.TMP_PLAYLIST_FILE)
                if file_age < settings.PLAYLIST_CACHE_EXPIRY:
                    try:
                        with open(settings.TMP_PLAYLIST_FILE, "r") as f:
                            cached_tracks = json.load(f)
                            if cached_tracks and isinstance(cached_tracks, list):
                                logger.debug(f"   ✅ Playlist loaded from cache")
                                logger.info(f"✅ {len(cached_tracks)} tracks found in cache")
                                return cached_tracks
                    except (json.JSONDecodeError, ValueError):
                        logger.debug(f"   ⚠️ Cache corrupted, fetching fresh...")
            
            # Fetch from Spotify
            logger.info(f"📋 Retrieving playlist...")
            logger.debug(f"   📡 Fetching from Spotify API...")
            
            results = self.client.playlist_tracks(playlist_id)
            all_tracks = self._extract_tracks_from_results(results)
            
            # Pagination
            page = 1
            while results.get("next"):
                page += 1
                logger.debug(f"   Page {page}...")
                results = self.client.next(results)
                all_tracks.extend(self._extract_tracks_from_results(results))
            
            # Cache results
            os.makedirs(settings.DATA_DIR, exist_ok=True)
            with open(settings.TMP_PLAYLIST_FILE, "w") as f:
                json.dump(all_tracks, f)
                logger.debug(f"   💾 Playlist cached to {settings.TMP_PLAYLIST_FILE}")
            
            logger.info(f"✅ {len(all_tracks)} tracks found in the playlist")
            
            # Show sample
            if all_tracks:
                logger.debug(f"   Examples:")
                for i, (title, artist) in enumerate(all_tracks[:3], 1):
                    logger.debug(f"      {i}. {title[:35]} - {artist[:20]}")
                if len(all_tracks) > 3:
                    logger.debug(f"      ... and {len(all_tracks) - 3} more")
            
            return all_tracks
            
        except Exception as e:
            logger.error(f"❌ Spotify error: {e}")
            return []
    
    @staticmethod
    def _extract_tracks_from_results(results: dict) -> List[Tuple[str, str]]:
        """
        Extract track information from Spotify API results.
        
        Args:
            results: Spotify API response
        
        Returns:
            List of (title, artist) tuples
        """
        tracks = [
            (item["track"]["name"], item["track"]["artists"][0]["name"])
            for item in results["items"]
            if item.get("track")
        ]
        return tracks
