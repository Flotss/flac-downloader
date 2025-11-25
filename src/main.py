"""Main entry point for the FLAC downloader application."""

import time
import os
from datetime import datetime

import pandas as pd

from src.config import settings
from src.core.logging import get_logger
from src.services import TidalAPI, SpotifyService, Downloader
from src.utils import ensure_directory_exists, list_audio_files, save_failed_downloads, get_error_cache

logger = get_logger()


class DownloadSession:
    """Manages a complete download session."""
    
    def __init__(self):
        """Initialize download session."""
        self.api = TidalAPI()
        self.spotify = SpotifyService()
        self.downloader = Downloader(self.api)
        self.failed_songs = []
        self.successful_count = 0
        self.start_time = None
    
    def run(self) -> None:
        """Execute the main download session."""
        # Setup
        ensure_directory_exists(settings.DOWNLOAD_FOLDER)
        ensure_directory_exists(settings.DATA_DIR)
        
        # Header
        print("\n")
        logger.info("═" * 60)
        logger.info("🎶 FLAC DOWNLOADER - DIRECT API VERSION 🎶")
        logger.info("═" * 60)
        logger.info(f"📂 Download folder: {settings.DOWNLOAD_FOLDER}")
        logger.info(f"📝 Failed log: {settings.CSV_LOG}")
        logger.info(f"🔄 Max retries per track: {settings.RETRY_MAX_COUNT}")
        logger.info("─" * 60)
        
        self.start_time = time.time()
        
        try:
            # Check existing files
            logger.info(f"📁 Analyzing destination folder...")
            existing_files = list_audio_files(settings.DOWNLOAD_FOLDER)
            logger.info(f"   {len(existing_files)} audio files already present")
            
            # Get playlist from Spotify
            tracks = self.spotify.get_playlist_tracks(settings.SPOTIFY_PLAYLIST_URL)
            
            if not tracks:
                logger.error("❌ No tracks to download. Exiting.")
                return
            
            # Filter already downloaded
            logger.info(f"🔍 Filtering already downloaded tracks...")
            filtered_tracks = []
            skipped_count = 0
            
            for title, artist in tracks:
                if not self.downloader.is_track_downloaded(title, artist, existing_files):
                    filtered_tracks.append((title, artist))
                else:
                    skipped_count += 1
            
            logger.info(f"   ⏭️  {skipped_count} tracks already downloaded (skipped)")
            logger.info(f"   📥 {len(filtered_tracks)} tracks to download")
            
            if not filtered_tracks:
                logger.info("✅ All tracks already downloaded!")
                return
            
            total_tracks = len(filtered_tracks)
            logger.info("─" * 60)
            logger.info(f"🚀 STARTING DOWNLOADS ({total_tracks} tracks)")
            logger.info("─" * 60)
            
            # Download each track
            for i, (title, artist) in enumerate(filtered_tracks, 1):
                logger.info(f"")
                logger.info(f"📊 Progress: [{i}/{total_tracks}] ({i/total_tracks*100:.1f}%)")
                
                logger.info(f"{'─'*50}")
                logger.info(f"🎵 Processing: {title[:35]} - {artist[:20]}")
                
                # Check if already in error cache (skip completely)
                if self.downloader.is_in_error_cache(title, artist):
                    error_cache = get_error_cache()
                    error_reason = error_cache.get_error_reason(title, artist)
                    logger.info(f"{'─'*50}")
                    logger.warning(f"⏭️ Skipping (in error cache): {error_reason}")
                    continue
                
                retry_count = 0
                status = ""
                track_id = 0
                
             
                # Retry loop
                while retry_count < settings.RETRY_MAX_COUNT:
                    status, track_id = self.downloader.download_song(title, artist)
                    
                    if status == "Success":
                        break
                    
                    retry_count += 1
                    if retry_count < settings.RETRY_MAX_COUNT:
                        logger.warning(f"🔄 Retry ({retry_count + 1}/{settings.RETRY_MAX_COUNT})...")
                        time.sleep(2)
                
                # Log result and handle caching
                error_cache = get_error_cache()
                if status == "Success":
                    self.successful_count += 1
                    logger.info(f"✅ [{i}/{total_tracks}] SUCCESS: {title[:40]}...")
                    # Refresh existing files
                    existing_files = list_audio_files(settings.DOWNLOAD_FOLDER)
                else:
                    # Determine error reason for caching
                    if "Song not found" in status:
                        error_reason = "Song not found"
                    elif "Download error" in status:
                        error_reason = "Download error"
                    else:
                        error_reason = status
                    
                    # Add to error cache AFTER all retries failed
                    error_cache.add_error(title, artist, error_reason)
                    
                    logger.error(f"❌ [{i}/{total_tracks}] FAILED: {title[:40]}... ({status})")
                    self.failed_songs.append({
                        "title": title,
                        "artist": artist,
                        "status": status,
                        "timestamp": pd.Timestamp.now()
                    })
                
                # Small delay between downloads
                time.sleep(0.5)
            
            # Final summary
            self._print_summary(total_tracks)
            
        except KeyboardInterrupt:
            logger.warning("\n\n⛔ User interrupted (Ctrl+C)")
            logger.info(f"   Downloaded before stop: {self.successful_count}")
            if self.failed_songs:
                save_failed_downloads(self.failed_songs)
            self._print_error_cache_summary()
        
        except Exception as e:
            logger.critical(f"💀 FATAL ERROR: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            self._print_error_cache_summary()
    
    def _print_summary(self, total_tracks: int) -> None:
        """Print session summary."""
        elapsed = time.time() - self.start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        
        logger.info("")
        logger.info("═" * 60)
        logger.info("📊 FINAL SUMMARY")
        logger.info("═" * 60)
        logger.info(f"   ⏱️  Total time: {elapsed_min}m {elapsed_sec}s")
        logger.info(f"   ✅ Successful: {self.successful_count}/{total_tracks}")
        logger.info(f"   ❌ Failed: {len(self.failed_songs)}/{total_tracks}")
        logger.info(f"   📈 Success rate: {self.successful_count/total_tracks*100:.1f}%")
        
        # API stats
        api_stats = self.api.get_stats()
        logger.info(f"   📡 API requests: {api_stats['total_requests']} (success: {api_stats['success_rate']}%)")
        
        if self.failed_songs:
            save_failed_downloads(self.failed_songs)
            logger.info(f"   📝 Failed downloads saved to: {settings.CSV_LOG}")
            logger.info(f"   💡 Tip: Re-run to retry failed downloads")
        else:
            logger.info(f"   🎉 All downloads successful!")
        
        # Error cache summary
        self._print_error_cache_summary()
        
        logger.info("═" * 60)
    
    def _print_error_cache_summary(self) -> None:
        """Print error cache summary."""
        error_cache = get_error_cache()
        
        if error_cache.get_failed_count() == 0:
            return
        
        logger.info("")
        logger.info("═" * 60)
        logger.info("💾 ERROR CACHE STATUS")
        logger.info("═" * 60)
        error_cache.print_summary()
        logger.info("═" * 60)


def main() -> None:
    """Main entry point."""
    try:
        settings.validate()
        session = DownloadSession()
        session.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
