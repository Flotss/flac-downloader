"""FLAC Downloader - Package initialization."""

__version__ = "2.0.0"
__author__ = "FLAC Downloader Team"
__description__ = "Download Spotify playlist tracks in FLAC quality via Tidal API"

from src.core import Track, StreamInfo, DownloaderException, SongNotFoundError, DownloadError
from src.services import TidalAPI, SpotifyService, Downloader

__all__ = [
    "Track",
    "StreamInfo",
    "DownloaderException",
    "SongNotFoundError",
    "DownloadError",
    "TidalAPI",
    "SpotifyService",
    "Downloader",
]
