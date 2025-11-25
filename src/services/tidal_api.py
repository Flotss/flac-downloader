"""Tidal API client for searching and downloading tracks."""

import base64
import json
import os
import random
import re
import time
from typing import List, Optional, Dict, Any

import requests

from src.config import settings, constants
from src.core.models import Track, StreamInfo
from src.core.exceptions import APIError, SongNotFoundError
from src.core.logging import get_logger

logger = get_logger()


class TidalAPI:
    """Client for Tidal API interactions with automatic server rotation."""
    
    def __init__(self, servers: Optional[List[str]] = None):
        """
        Initialize Tidal API client.
        
        Args:
            servers: List of API servers (uses defaults if not provided)
        """
        self.servers = servers or constants.API_SERVERS
        self.session = requests.Session()
        self.session.headers.update(constants.HTTP_HEADERS)
        self.current_server_index = 0
        
        # Statistics
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        logger.info(f"🚀 API initialized with {len(self.servers)} servers")
    
    def _get_random_server(self) -> str:
        """Get a random server from the list."""
        return random.choice(self.servers)
    
    def _rotate_server(self) -> str:
        """Rotate to next server for load balancing."""
        self.current_server_index = (self.current_server_index + 1) % len(self.servers)
        return self.servers[self.current_server_index]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get API statistics.
        
        Returns:
            Dictionary with request statistics
        """
        return {
            "total_requests": self.request_count,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "success_rate": round(self.successful_requests / max(self.request_count, 1) * 100, 1)
        }
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with automatic server rotation on failure.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            max_retries: Number of retry attempts
        
        Returns:
            JSON response or None if all retries fail
        """
        self.request_count += 1
        last_error = None
        servers_tried = set()
        
        logger.debug(f"📡 Request: {endpoint} | Params: {params}")
        
        for attempt in range(max_retries * len(self.servers)):
            server = self._get_random_server()
            if server in servers_tried:
                server = self._rotate_server()
            servers_tried.add(server)
            
            url = f"{server}{endpoint}"
            server_name = server.split('//')[1]
            
            try:
                start_time = time.time()
                response = self.session.get(
                    url,
                    params=params,
                    timeout=constants.API_REQUEST_TIMEOUT
                )
                elapsed = time.time() - start_time
                
                # Handle rate limiting
                if response.status_code == 429:
                    logger.warning(f"⏳ Rate limit on {server_name} - waiting 5s...")
                    time.sleep(constants.API_RATE_LIMIT_WAIT)
                    continue
                
                # Success
                if response.status_code == 200:
                    self.successful_requests += 1
                    logger.debug(f"   ✅ {server_name} - {elapsed:.2f}s")
                    return response.json()
                
                # Server error - retry
                if response.status_code >= 500:
                    logger.warning(f"   🔥 {server_name}: error {response.status_code}")
                    time.sleep(constants.API_RETRY_WAIT)
                    continue
                
                # Not found
                if response.status_code == 404:
                    logger.debug(f"   📭 Not found (404)")
                    return None
                
                last_error = f"HTTP {response.status_code}"
                logger.debug(f"   ⚠️ {server_name}: {last_error}")
                
            except requests.exceptions.Timeout:
                logger.warning(f"   ⏱️ Timeout on {server_name}")
                time.sleep(constants.API_RETRY_WAIT)
                continue
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning(f"   💥 {server_name}: {e}")
                time.sleep(constants.API_RETRY_WAIT)
                continue
        
        self.failed_requests += 1
        if last_error:
            logger.error(f"❌ Failed after {len(servers_tried)} servers: {last_error}")
        return None
    
    def search_tracks(self, query: str) -> List[Track]:
        """
        Search for tracks by query.
        
        Args:
            query: Search query string
        
        Returns:
            List of Track objects
        """
        data = self._make_request("/search/", params={"s": query[:100]})
        
        if not data:
            return []
        
        tracks = []
        items = []
        
        # Handle different response formats
        if isinstance(data, dict):
            if "tracks" in data:
                items = data["tracks"].get("items", []) if isinstance(data["tracks"], dict) else data["tracks"]
            elif "items" in data:
                items = data["items"]
        elif isinstance(data, list):
            items = data
        
        for item in items[:10]:  # Limit to 10 results
            try:
                track = self._parse_track(item)
                if track:
                    tracks.append(track)
            except Exception as e:
                logger.debug(f"Parse error: {e}")
                continue
        
        return tracks
    
    def _parse_track(self, item: Dict[str, Any]) -> Optional[Track]:
        """
        Parse track data from API response.
        
        Args:
            item: Track data from API
        
        Returns:
            Track object or None if parsing fails
        """
        if not item or not isinstance(item, dict):
            return None
        
        track_id = item.get("id")
        title = item.get("title", "")
        
        # Extract artist name
        artists = item.get("artists", [])
        if artists and isinstance(artists, list):
            artist = artists[0].get("name", "") if isinstance(artists[0], dict) else str(artists[0])
        else:
            artist = item.get("artist", {}).get("name", "") if isinstance(item.get("artist"), dict) else ""
        
        # Extract album info
        album_data = item.get("album", {})
        album = album_data.get("title", "") if isinstance(album_data, dict) else ""
        cover_id = album_data.get("cover", "") if isinstance(album_data, dict) else ""
        
        duration = item.get("duration", 0)
        quality = item.get("audioQuality", "LOSSLESS")
        
        if not track_id or not title:
            return None
        
        return Track(
            id=int(track_id),
            title=title,
            artist=artist,
            album=album,
            duration=duration,
            quality=quality,
            cover_id=cover_id
        )
    
    def get_track_stream(self, track_id: int, quality: str = "LOSSLESS") -> Optional[StreamInfo]:
        """
        Get stream URL for a specific track.
        
        Args:
            track_id: Track ID
            quality: Audio quality (default: LOSSLESS)
        
        Returns:
            StreamInfo object or None if retrieval fails
        """
        data = self._make_request("/track/", params={"id": track_id, "quality": quality})
        
        if not data:
            return None
        
        # Parse response (can be list or dict)
        track_data = data[0] if isinstance(data, list) and len(data) > 0 else data
        info_data = data[1] if isinstance(data, list) and len(data) > 1 else data.get("info", {})
        
        track = self._parse_track(track_data) or Track(
            id=track_id,
            title="Unknown",
            artist="Unknown",
            album="Unknown",
            duration=0,
            quality=quality
        )
        
        # Extract stream URL
        stream_url = None
        manifest = info_data.get("manifest", "") if isinstance(info_data, dict) else ""
        
        # Try direct URL first
        if isinstance(data, list) and len(data) > 2:
            stream_url = data[2] if isinstance(data[2], str) else None
        elif isinstance(data, dict):
            stream_url = data.get("originalTrackUrl")
        
        # Decode manifest if no direct URL
        if not stream_url and manifest:
            stream_url = self._extract_url_from_manifest(manifest)
        
        if not stream_url:
            return None
        
        return StreamInfo(track=track, stream_url=stream_url, manifest=manifest)
    
    def get_song_direct(self, query: str, quality: str = "LOSSLESS") -> Optional[StreamInfo]:
        """
        Search and get stream URL in one direct request.
        
        Args:
            query: Search query
            quality: Audio quality
        
        Returns:
            StreamInfo object or None
        """
        logger.debug(f"⚡ Direct /song/ endpoint for: \"{query[:40]}...\"")
        data = self._make_request("/song/", params={"q": query[:100], "quality": quality})
        
        if not data:
            logger.debug(f"   📭 No response from /song/")
            return None
        
        # Handle list response
        if isinstance(data, list):
            if len(data) == 0:
                logger.debug(f"   📭 Empty list response")
                return None
            
            track_data = data[0] if len(data) > 0 else {}
            info_data = data[1] if len(data) > 1 else {}
            direct_url = data[2] if len(data) > 2 and isinstance(data[2], str) else None
            
            stream_url = direct_url
            if not stream_url and isinstance(info_data, dict):
                manifest = info_data.get("manifest", "")
                if manifest:
                    stream_url = self._extract_url_from_manifest(manifest)
            
            if not stream_url:
                logger.debug(f"   ❌ No URL in list response")
                return None
            
            track = self._parse_track(track_data) or Track(
                id=0,
                title=query,
                artist="",
                album="",
                duration=0,
                quality=quality
            )
            logger.info(f"   ✅ Found via /song/: {track.title[:30]} - {track.artist[:20]}")
            return StreamInfo(track=track, stream_url=stream_url)
        
        # Handle dict response
        elif isinstance(data, dict):
            stream_url = data.get("url") or data.get("stream_url")
            if not stream_url:
                manifest = data.get("manifest", "")
                if manifest:
                    stream_url = self._extract_url_from_manifest(manifest)
            
            if not stream_url:
                logger.debug(f"   ❌ No URL in dict response")
                return None
            
            track = Track(
                id=data.get("id", 0),
                title=data.get("title", query),
                artist=data.get("artist", ""),
                album=data.get("album", ""),
                duration=data.get("duration", 0),
                quality=quality,
                cover_id=data.get("cover")
            )
            
            logger.info(f"   ✅ Found via /song/: {track.title[:30]}")
            return StreamInfo(track=track, stream_url=stream_url)
        
        return None
    
    def _extract_url_from_manifest(self, manifest: str) -> Optional[str]:
        """
        Extract stream URL from base64 encoded manifest.
        
        Args:
            manifest: Base64 encoded manifest string
        
        Returns:
            Stream URL or None
        """
        try:
            decoded = base64.b64decode(manifest).decode('utf-8')
            logger.debug(f"      Decoded manifest: {len(decoded)} chars")
            
            # Try JSON parsing first
            try:
                parsed = json.loads(decoded)
                if isinstance(parsed, dict) and "urls" in parsed:
                    urls = parsed["urls"]
                    if isinstance(urls, list) and len(urls) > 0:
                        logger.debug(f"      ✅ URL extracted from JSON manifest")
                        return urls[0]
            except json.JSONDecodeError:
                logger.debug(f"      Non-JSON manifest, trying regex...")
            
            # Fallback to regex
            match = re.search(r'https?://[\w\-.~:?#\[\]@!$&\'()*+,;=%/]+', decoded)
            if match:
                logger.debug(f"      ✅ URL extracted via regex")
                return match.group(0)
            
        except Exception as e:
            logger.error(f"      ❌ Manifest decode error: {e}")
        
        return None
    
    def download_cover(self, cover_id: str, filepath: str) -> bool:
        """
        Download album cover from Tidal resources.
        
        Args:
            cover_id: Cover ID from album metadata (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
            filepath: Destination file path for cover image
        
        Returns:
            True if download successful
        """
        if not cover_id:
            logger.debug("   ℹ️ No cover ID provided")
            return False
        
        # Build Tidal cover URL
        # Convert UUID: 2b3c28fe-bfb8-48b1-9ad7-f912847f3d71 -> 2b3c28fe/bfb8/48b1/9ad7/f912847f3d71
        parts = cover_id.split('-')
        if len(parts) != 5:
            logger.debug(f"   ⚠️ Invalid cover ID format: {cover_id}")
            return False
        
        cover_url = f"https://resources.tidal.com/images/{'/'.join(parts)}/1280x1280.jpg"
        logger.debug(f"🖼️ Downloading cover: {cover_url}")
        
        try:
            response = self.session.get(
                cover_url,
                timeout=settings.DOWNLOAD_TIMEOUT,
                stream=True
            )
            response.raise_for_status()
            
            # Write cover file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            logger.debug(f"   ✅ Cover saved: {file_size / 1024:.1f} KB")
            return True
        
        except Exception as e:
            logger.warning(f"   ⚠️ Cover download failed: {e}")
            # Not critical - don't fail the whole process
            return False
    
    def download_track(self, stream_url: str, filepath: str) -> bool:
        """
        Download a track from stream URL.
        
        Args:
            stream_url: URL to download from
            filepath: Destination file path
        
        Returns:
            True if download succeeds
        """
        filename = filepath.split('/')[-1]
        logger.info(f"📥 Downloading: {filename[:50]}...")
        logger.debug(f"   Source: {stream_url[:70]}...")
        logger.debug(f"   Destination: {filepath}")
        
        try:
            start_time = time.time()
            response = self.session.get(
                stream_url,
                stream=True,
                timeout=settings.DOWNLOAD_TIMEOUT
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            if total_size:
                logger.info(f"   📦 Size: {total_size / 1024 / 1024:.2f} MB")
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            progress = (downloaded / total_size) * 100
                            bar_length = 30
                            filled = int(bar_length * downloaded / total_size)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            print(f"\r   [{bar}] {progress:.1f}%", end="", flush=True)
            
            elapsed = time.time() - start_time
            speed = (downloaded / 1024 / 1024) / elapsed if elapsed > 0 else 0
            print()  # New line after progress
            
            # Verify download
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                final_size = os.path.getsize(filepath) / 1024 / 1024
                logger.info(f"   ✅ Complete! {final_size:.2f} MB in {elapsed:.1f}s ({speed:.2f} MB/s)")
                return True
            
        except requests.exceptions.Timeout:
            logger.error(f"   ⏱️ Timeout after {settings.DOWNLOAD_TIMEOUT}s")
        except requests.exceptions.HTTPError as e:
            logger.error(f"   🔥 HTTP error: {e}")
        except Exception as e:
            logger.error(f"   💥 Error: {e}")
        
        # Cleanup on failure
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"   🗑️ Partial file deleted")
        
        return False


