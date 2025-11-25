"""Custom exceptions for the downloader."""


class DownloaderException(Exception):
    """Base exception for all downloader errors."""
    pass


class SongNotFoundError(DownloaderException):
    """Raised when a song cannot be found via API."""
    pass


class DownloadError(DownloaderException):
    """Raised when a track download fails."""
    pass


class APIError(DownloaderException):
    """Raised when API communication fails."""
    pass
