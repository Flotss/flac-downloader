"""Tests for cover download functionality."""

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.services.tidal_api import TidalAPI
from src.services.metadata import MetadataManager
from src.core.models import Track


class TestCoverDownload:
    """Test cover download functionality."""
    
    def test_cover_url_construction(self):
        """Test that cover URL is constructed correctly from cover_id."""
        api = TidalAPI()
        
        # UUID format: 2b3c28fe-bfb8-48b1-9ad7-f912847f3d71
        # Should become: 2b3c28fe/bfb8/48b1/9ad7/f912847f3d71
        cover_id = "2b3c28fe-bfb8-48b1-9ad7-f912847f3d71"
        expected_url = "https://resources.tidal.com/images/2b3c28fe/bfb8/48b1/9ad7/f912847f3d71/1280x1280.jpg"
        
        # We'll verify by patching the session.get method
        with patch.object(api.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b'test_data']
            mock_get.return_value = mock_response
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                temp_cover = f.name
            
            try:
                api.download_cover(cover_id, temp_cover)
                mock_get.assert_called_once()
                called_url = mock_get.call_args[0][0]
                assert called_url == expected_url
            finally:
                if os.path.exists(temp_cover):
                    os.remove(temp_cover)
    
    def test_invalid_cover_id_format(self):
        """Test that invalid cover IDs are rejected."""
        api = TidalAPI()
        
        # Invalid format (not enough parts)
        invalid_cover_id = "2b3c28fe-bfb8-48b1"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            temp_cover = f.name
        
        try:
            result = api.download_cover(invalid_cover_id, temp_cover)
            assert result is False
        finally:
            if os.path.exists(temp_cover):
                os.remove(temp_cover)
    
    def test_empty_cover_id(self):
        """Test that empty cover IDs are handled gracefully."""
        api = TidalAPI()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            temp_cover = f.name
        
        try:
            result = api.download_cover("", temp_cover)
            assert result is False
        finally:
            if os.path.exists(temp_cover):
                os.remove(temp_cover)
    
    def test_add_cover_to_metadata(self):
        """Test adding cover to FLAC metadata."""
        try:
            from mutagen.flac import FLAC
        except ImportError:
            pytest.skip("mutagen not installed")

        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test FLAC file
            flac_path = os.path.join(tmpdir, 'test.flac')
            cover_path = os.path.join(tmpdir, 'cover.jpg')

            # Créer un fichier FLAC minimal valide (nécessite flac et sox installés)
            wav_path = os.path.join(tmpdir, 'test.wav')
            # Générer un fichier wav silencieux
            subprocess.run(["sox", "-n", "-r", "44100", "-c", "2", wav_path, "trim", "0.0", "0.1"], check=True)
            # Convertir en FLAC
            subprocess.run(["flac", wav_path, "-o", flac_path], check=True)

            audio = FLAC(flac_path)
            audio.save(flac_path)
            
            # Create fake cover image
            with open(cover_path, 'wb') as f:
                f.write(b'\xFF\xD8\xFF\xE0')  # JPEG header
            
            # Add metadata with cover
            result = MetadataManager.add_track_metadata(
                flac_path,
                track_id=12345,
                title="Test Song",
                artist="Test Artist",
                album="Test Album",
                cover_path=cover_path
            )
            
            assert result is True
            
            # Verify metadata was added
            audio = FLAC(flac_path)
            assert audio["TRACK_ID"] == ["12345"]
            assert audio["TITLE"] == ["Test Song"]
            assert audio["ARTIST"] == ["Test Artist"]
            assert audio["ALBUM"] == ["Test Album"]


class TestTrackModelWithCover:
    """Test Track model with cover support."""
    
    def test_track_with_cover_id(self):
        """Test Track dataclass with cover_id."""
        cover_id = "2b3c28fe-bfb8-48b1-9ad7-f912847f3d71"
        track = Track(
            id=59727867,
            title="ALL NIGHT",
            artist="Beyoncé",
            album="LEMONADE",
            duration=322,
            quality="LOSSLESS",
            cover_id=cover_id
        )
        
        assert track.cover_id == cover_id
        assert track.id == 59727867
        assert str(track) == "Beyoncé - ALL NIGHT"
    
    def test_track_without_cover_id(self):
        """Test Track dataclass without cover_id."""
        track = Track(
            id=12345,
            title="Song Title",
            artist="Artist Name",
            album="Album Name",
            duration=180,
            quality="LOSSLESS"
        )
        
        assert track.cover_id is None
