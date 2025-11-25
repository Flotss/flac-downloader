"""Test configuration for pytest."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def sample_track():
    """Create a sample track for testing."""
    from src.core.models import Track
    
    return Track(
        id=123,
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        duration=180,
        quality="LOSSLESS"
    )


@pytest.fixture
def sample_stream_info(sample_track):
    """Create sample stream info for testing."""
    from src.core.models import StreamInfo
    
    return StreamInfo(
        track=sample_track,
        stream_url="https://example.com/song.flac"
    )
