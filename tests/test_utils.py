"""Test suite for FLAC downloader."""

import pytest
from unittest.mock import Mock, patch

from src.core.models import Track, StreamInfo
from src.utils.text import normalize_track_name, sanitize_filename, get_normalized_words
from src.config import settings


class TestTrackModel:
    """Tests for Track model."""
    
    def test_track_creation(self):
        """Test creating a Track instance."""
        track = Track(
            id=1,
            title="Song",
            artist="Artist",
            album="Album",
            duration=180,
            quality="LOSSLESS"
        )
        assert track.id == 1
        assert track.title == "Song"
        assert str(track) == "Artist - Song"
    
    def test_track_with_cover(self):
        """Test Track with cover ID."""
        track = Track(
            id=1,
            title="Song",
            artist="Artist",
            album="Album",
            duration=180,
            quality="LOSSLESS",
            cover_id="abc123"
        )
        assert track.cover_id == "abc123"


class TestStreamInfoModel:
    """Tests for StreamInfo model."""
    
    def test_stream_info_creation(self):
        """Test creating a StreamInfo instance."""
        track = Track(
            id=1, title="Song", artist="Artist",
            album="Album", duration=180, quality="LOSSLESS"
        )
        stream_info = StreamInfo(
            track=track,
            stream_url="https://example.com/song.flac"
        )
        assert stream_info.track == track
        assert stream_info.stream_url == "https://example.com/song.flac"
        assert stream_info.manifest is None


class TestTextUtils:
    """Tests for text utility functions."""
    
    def test_normalize_track_name(self):
        """Test track name normalization."""
        # Basic normalization
        assert normalize_track_name("Song (Remix)") == "song"
        assert normalize_track_name("My Song - Feat. Artist") == "my song"
        assert normalize_track_name("UPPERCASE") == "uppercase"
    
    def test_normalize_with_versions(self):
        """Test normalization removes version indicators."""
        assert normalize_track_name("Song (Radio Mix)") == "song"
        assert normalize_track_name("Song [Remix Version]") == "song"
        assert normalize_track_name("Song ft. Artist") == "song"
    
    def test_get_normalized_words(self):
        """Test getting normalized word set."""
        words = get_normalized_words("My Amazing Song")
        assert "my" in words
        assert "amazing" in words
        assert "song" in words
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("Song: Title") == "Song Title"
        assert sanitize_filename("Artist - Song") == "Artist - Song"
        assert '"Bad"' not in sanitize_filename('Song "Quote"')
    
    def test_sanitize_filename_length(self):
        """Test filename length limiting."""
        long_name = "A" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 200


class TestSettings:
    """Tests for settings configuration."""
    
    def test_settings_defaults(self):
        """Test default settings are loaded."""
        assert settings.DOWNLOAD_TIMEOUT == 120
        assert settings.RETRY_MAX_COUNT == 3
        assert len(settings.VALID_AUDIO_EXTENSIONS) == 4
    
    def test_valid_extensions(self):
        """Test valid audio extensions are configured."""
        assert ".flac" in settings.VALID_AUDIO_EXTENSIONS
        assert ".mp3" in settings.VALID_AUDIO_EXTENSIONS
        assert ".m4a" in settings.VALID_AUDIO_EXTENSIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
