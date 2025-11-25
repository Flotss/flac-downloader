"""Tests for the error cache module."""

import os
import json
import tempfile
import pytest

from src.utils.error_cache import ErrorCache


@pytest.fixture
def temp_cache_file():
    """Create a temporary cache file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    yield temp_file
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture
def error_cache(temp_cache_file):
    """Create an error cache instance with temp file."""
    return ErrorCache(cache_file=temp_cache_file)


def test_add_and_check_error(error_cache):
    """Test adding and checking failed tracks."""
    error_cache.add_error("Test Track", "Test Artist", "Not found")
    
    assert error_cache.is_failed("Test Track", "Test Artist")
    assert error_cache.get_error_reason("Test Track", "Test Artist") == "Not found"


def test_normalization_case_insensitive(error_cache):
    """Test that track checking is case-insensitive."""
    error_cache.add_error("Test Track", "Test Artist", "Error")
    
    # Different cases should still match
    assert error_cache.is_failed("test track", "test artist")
    assert error_cache.is_failed("TEST TRACK", "TEST ARTIST")
    assert error_cache.is_failed("Test Track", "Test Artist")


def test_normalization_whitespace(error_cache):
    """Test that track checking handles whitespace variations."""
    error_cache.add_error("Test  Track", "Test  Artist", "Error")
    
    # Extra spaces should still match
    assert error_cache.is_failed("Test Track", "Test Artist")
    assert error_cache.is_failed("  Test Track  ", "  Test Artist  ")


def test_failed_track_not_found(error_cache):
    """Test checking for tracks that don't exist."""
    assert not error_cache.is_failed("Unknown Track", "Unknown Artist")
    assert error_cache.get_error_reason("Unknown Track", "Unknown Artist") == ""


def test_get_failed_tracks(error_cache):
    """Test retrieving all failed tracks."""
    error_cache.add_error("Track 1", "Artist 1", "Not found")
    error_cache.add_error("Track 2", "Artist 2", "Download error")
    
    failed_tracks = error_cache.get_failed_tracks()
    assert len(failed_tracks) == 2
    assert any(t["title"] == "Track 1" for t in failed_tracks)
    assert any(t["title"] == "Track 2" for t in failed_tracks)


def test_get_failed_count(error_cache):
    """Test getting count of failed tracks."""
    assert error_cache.get_failed_count() == 0
    
    error_cache.add_error("Track 1", "Artist 1", "Error 1")
    assert error_cache.get_failed_count() == 1
    
    error_cache.add_error("Track 2", "Artist 2", "Error 2")
    assert error_cache.get_failed_count() == 2


def test_get_failed_count_by_reason(error_cache):
    """Test counting failures by reason."""
    error_cache.add_error("Track 1", "Artist 1", "Not found")
    error_cache.add_error("Track 2", "Artist 2", "Not found")
    error_cache.add_error("Track 3", "Artist 3", "Download error")
    
    reasons = error_cache.get_failed_count_by_reason()
    assert reasons["Not found"] == 2
    assert reasons["Download error"] == 1


def test_clear_error(error_cache):
    """Test clearing a specific error."""
    error_cache.add_error("Track 1", "Artist 1", "Error")
    assert error_cache.is_failed("Track 1", "Artist 1")
    
    success = error_cache.clear_error("Track 1", "Artist 1")
    assert success
    assert not error_cache.is_failed("Track 1", "Artist 1")


def test_clear_error_not_found(error_cache):
    """Test clearing an error that doesn't exist."""
    success = error_cache.clear_error("Unknown", "Unknown")
    assert not success


def test_clear_all(error_cache):
    """Test clearing all errors."""
    error_cache.add_error("Track 1", "Artist 1", "Error 1")
    error_cache.add_error("Track 2", "Artist 2", "Error 2")
    assert error_cache.get_failed_count() == 2
    
    error_cache.clear_all()
    assert error_cache.get_failed_count() == 0


def test_persistence(temp_cache_file):
    """Test that cache persists between instances."""
    # Create first cache and add error
    cache1 = ErrorCache(cache_file=temp_cache_file)
    cache1.add_error("Track 1", "Artist 1", "Error")
    
    # Create second cache with same file
    cache2 = ErrorCache(cache_file=temp_cache_file)
    
    # Should be able to find the error
    assert cache2.is_failed("Track 1", "Artist 1")
    assert cache2.get_error_reason("Track 1", "Artist 1") == "Error"


def test_increment_attempts(error_cache):
    """Test that attempts counter increments."""
    error_cache.add_error("Track 1", "Artist 1", "Error")
    assert error_cache.errors["track 1|artist 1"]["attempts"] == 1
    
    # Add same error again
    error_cache.add_error("Track 1", "Artist 1", "Error")
    assert error_cache.errors["track 1|artist 1"]["attempts"] == 2


def test_timestamp_recorded(error_cache):
    """Test that timestamp is recorded for each error."""
    error_cache.add_error("Track 1", "Artist 1", "Error")
    
    error_info = error_cache.errors["track 1|artist 1"]
    assert "timestamp" in error_info
    assert error_info["timestamp"] > 0


def test_corrupted_cache_file(temp_cache_file):
    """Test handling of corrupted cache file."""
    # Write invalid JSON
    with open(temp_cache_file, 'w') as f:
        f.write("{ invalid json }")
    
    # Should start fresh without error
    cache = ErrorCache(cache_file=temp_cache_file)
    assert cache.get_failed_count() == 0


def test_cache_file_creation(temp_cache_file):
    """Test that cache file is created if it doesn't exist."""
    # S'assurer que le fichier n'existe pas avant le test
    if os.path.exists(temp_cache_file):
        os.remove(temp_cache_file)
    assert not os.path.exists(temp_cache_file)
    
    # Create cache and add error
    cache = ErrorCache(cache_file=temp_cache_file)
    cache.add_error("Track 1", "Artist 1", "Error")
    
    # File should now exist
    assert os.path.exists(temp_cache_file)
    
    # Verify it's valid JSON
    with open(temp_cache_file, 'r') as f:
        data = json.load(f)
        assert len(data) == 1
