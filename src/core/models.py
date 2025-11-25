"""Data models for tracks and stream information."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    """Represents a music track with metadata."""
    
    id: int
    title: str
    artist: str
    album: str
    duration: int
    quality: str
    cover_id: Optional[str] = None
    
    def __str__(self) -> str:
        """Return string representation of track."""
        return f"{self.artist} - {self.title}"


@dataclass
class StreamInfo:
    """Contains stream information for a track."""
    
    track: Track
    stream_url: str
    manifest: Optional[str] = None
