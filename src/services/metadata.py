"""Metadata management for audio files."""

import os
from typing import Optional

from src.core.logging import get_logger

logger = get_logger()

try:
    from mutagen.flac import FLAC, Picture
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False
    logger.warning("⚠️ mutagen not installed. Install it with: pip install mutagen")


class MetadataManager:
    """Manager for audio file metadata."""
    
    @staticmethod
    def add_track_metadata(filepath: str, track_id: int, title: str, artist: str, album: str = "", cover_path: Optional[str] = None) -> bool:
        """
        Add track metadata to FLAC file tags including cover art.
        
        Args:
            filepath: Path to FLAC file
            track_id: Track ID
            title: Track title
            artist: Artist name
            album: Album name (optional)
            cover_path: Path to cover image file (optional)
        
        Returns:
            True if metadata added successfully
        """
        if not HAS_MUTAGEN:
            logger.warning(f"   ⚠️ mutagen not available, skipping metadata tags")
            return False
        
        try:
            from datetime import datetime
            
            audio = FLAC(filepath)
            audio["TRACK_ID"] = str(track_id)
            audio["TITLE"] = title
            audio["ARTIST"] = artist
            if album:
                audio["ALBUM"] = album
            audio["DATE_DOWNLOADED"] = datetime.now().isoformat()
            
            # Add cover art if provided
            if cover_path and os.path.exists(cover_path):
                try:
                    # Create FLAC Picture object with cover data
                    pic = Picture()
                    pic.type = 3  # Cover (front)
                    pic.desc = "Cover"
                    pic.mime = "image/jpeg"
                    
                    # Read cover image data
                    with open(cover_path, 'rb') as f:
                        pic.data = f.read()
                    
                    audio.add_picture(pic)
                    logger.debug(f"   📸 Cover art added ({len(pic.data) / 1024:.1f} KB)")
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not add cover art: {e}")
            
            audio.save()
            logger.debug(f"   📝 FLAC tags saved: track_id={track_id}")
            return True
        except Exception as e:
            logger.warning(f"   ⚠️ Error adding FLAC tags: {e}")
            return False
    
    @staticmethod
    def get_track_id(filepath: str) -> Optional[int]:
        """
        Extract track_id from FLAC file tags.
        
        Args:
            filepath: Path to FLAC file
        
        Returns:
            Track ID or None if not found
        """
        if not HAS_MUTAGEN:
            return None
        
        try:
            audio = FLAC(filepath)
            if "TRACK_ID" in audio:
                return int(audio["TRACK_ID"][0])
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def has_track_id(track_id: int, folder: str) -> bool:
        """
        Check if track is already downloaded by checking FLAC tags.
        
        Args:
            track_id: Track ID to search for
            folder: Folder to search in
        
        Returns:
            True if track with this ID already exists
        """
        import os
        from src.config import settings
        
        if not os.path.isdir(folder):
            return False
        
        try:
            for filename in os.listdir(folder):
                if filename.lower().endswith(settings.VALID_AUDIO_EXTENSIONS):
                    filepath = os.path.join(folder, filename)
                    file_track_id = MetadataManager.get_track_id(filepath)
                    if file_track_id == track_id:
                        logger.debug(f"   ✅ Track {track_id} already downloaded: {filename}")
                        return True
        except Exception:
            pass
        
        return False
