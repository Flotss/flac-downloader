"""Configuration management for the application."""

import os
import logging


class Settings:
    """Application settings loaded from environment variables."""

    # Paths
    DOWNLOAD_FOLDER: str = os.getenv("DOWNLOAD_FOLDER", "/home/flotss/Musique/Flac_songs")
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    CSV_LOG: str = os.path.join(DATA_DIR, "download_log.csv")
    TMP_PLAYLIST_FILE: str = os.path.join(DATA_DIR, "tmp_spotify_playlist.json")
    DATABASE_FILE: str = os.getenv("DATABASE_FILE", "dreamlight.db")

    # Spotify
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "TO_DEFINE_YOUR_OWN_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: str = os.getenv(
        "SPOTIFY_CLIENT_SECRET", "TO_DEFINE_YOUR_OWN_CLIENT_SECRET"
    )
    SPOTIFY_PLAYLIST_URL: str = os.getenv(
        "SPOTIFY_PLAYLIST_URL",
        "https://open.spotify.com/playlist/37i9dQZF1DWTcqUzwhNmKv?si=752ed89004684b3c"
    )

    # Download
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "120"))
    RETRY_MAX_COUNT: int = int(os.getenv("RETRY_MAX_COUNT", "3"))
    VALID_AUDIO_EXTENSIONS: tuple = (".flac", ".mp3", ".m4a", ".wav")

    # API
    PLAYLIST_CACHE_EXPIRY: int = int(os.getenv("PLAYLIST_CACHE_EXPIRY", "3600"))  # 1 hour
    ERROR_CACHE_FILE: str = os.path.join(DATA_DIR, "error_cache.json")
    ERROR_CACHE_EXPIRY: int = int(os.getenv("ERROR_CACHE_EXPIRY", "86400"))  # 24 hours

    # Logging
    _LOG_LEVEL_STR: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_LEVEL: int = getattr(logging, _LOG_LEVEL_STR, logging.INFO)

    @classmethod
    def validate(cls) -> None:
        """Validate critical settings."""
        if not cls.SPOTIFY_CLIENT_ID or not cls.SPOTIFY_CLIENT_SECRET:
            raise ValueError(
                "Spotify credentials not configured. "
                "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET"
            )


# Global settings instance
settings = Settings()
