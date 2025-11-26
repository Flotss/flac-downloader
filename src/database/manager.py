"""SQLite database manager for track data management."""

import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

from src.config import settings
from src.core.logging import get_logger

logger = get_logger()


class DatabaseManager:
    """Manages SQLite database for tracks, downloads, and error cache."""

    def __init__(self, db_path: str = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file (uses default if not provided)
        """
        self.db_path = db_path or os.path.join(
            settings.DATA_DIR, settings.DATABASE_FILE
        )
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Playlists table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spotify_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    track_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tracks table (tracks from playlists)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT,
                    status TEXT DEFAULT 'pending',
                    tidal_id INTEGER,
                    file_path TEXT,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    downloaded_at TIMESTAMP,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
                    UNIQUE(playlist_id, title, artist)
                )
            """)

            # Downloads history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    quality TEXT DEFAULT 'FLAC',
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (track_id) REFERENCES tracks(id)
                )
            """)

            # Error cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    error_reason TEXT NOT NULL,
                    attempts INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(title, artist)
                )
            """)

            # Create indexes for better performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tracks_status ON tracks(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tracks_playlist ON tracks(playlist_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_error_cache ON error_cache(title, artist)"
            )

            logger.debug("Database initialized successfully")

    # ============ Playlist Methods ============

    def add_playlist(
        self, spotify_id: str, name: str, url: str, track_count: int = 0
    ) -> int:
        """
        Add or update a playlist.

        Args:
            spotify_id: Spotify playlist ID
            name: Playlist name
            url: Playlist URL
            track_count: Number of tracks

        Returns:
            Playlist ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO playlists (spotify_id, name, url, track_count, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(spotify_id) DO UPDATE SET
                    name = excluded.name,
                    url = excluded.url,
                    track_count = excluded.track_count,
                    updated_at = CURRENT_TIMESTAMP
            """, (spotify_id, name, url, track_count))

            cursor.execute(
                "SELECT id FROM playlists WHERE spotify_id = ?", (spotify_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_playlists(self) -> List[Dict]:
        """Get all playlists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*,
                       COUNT(t.id) as total_tracks,
                       SUM(CASE WHEN t.status = 'downloaded' THEN 1 ELSE 0 END)
                           as downloaded_count,
                       SUM(CASE WHEN t.status = 'error' THEN 1 ELSE 0 END)
                           as error_count
                FROM playlists p
                LEFT JOIN tracks t ON p.id = t.playlist_id
                GROUP BY p.id
                ORDER BY p.updated_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_playlist(self, playlist_id: int) -> Optional[Dict]:
        """Get a specific playlist by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist and its tracks."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tracks WHERE playlist_id = ?", (playlist_id,))
            cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            return cursor.rowcount > 0

    # ============ Track Methods ============

    def add_track(
        self, playlist_id: int, title: str, artist: str, album: str = None
    ) -> int:
        """
        Add a track to a playlist.

        Args:
            playlist_id: Playlist ID
            title: Track title
            artist: Artist name
            album: Album name (optional)

        Returns:
            Track ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tracks (playlist_id, title, artist, album, status)
                VALUES (?, ?, ?, ?, 'pending')
                ON CONFLICT(playlist_id, title, artist) DO UPDATE SET
                    album = COALESCE(excluded.album, album)
            """, (playlist_id, title, artist, album))

            cursor.execute(
                "SELECT id FROM tracks WHERE playlist_id = ? AND title = ? AND artist = ?",
                (playlist_id, title, artist)
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def add_tracks_batch(self, playlist_id: int, tracks: List[Tuple[str, str]]) -> int:
        """
        Add multiple tracks to a playlist.

        Args:
            playlist_id: Playlist ID
            tracks: List of (title, artist) tuples

        Returns:
            Number of tracks added
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            added = 0
            for title, artist in tracks:
                cursor.execute("""
                    INSERT INTO tracks (playlist_id, title, artist, status)
                    VALUES (?, ?, ?, 'pending')
                    ON CONFLICT(playlist_id, title, artist) DO NOTHING
                """, (playlist_id, title, artist))
                added += cursor.rowcount
            return added

    def get_tracks(
        self, playlist_id: int = None, status: str = None
    ) -> List[Dict]:
        """
        Get tracks with optional filtering.

        Args:
            playlist_id: Filter by playlist (optional)
            status: Filter by status (optional)

        Returns:
            List of track dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT t.*, p.name as playlist_name
                FROM tracks t
                LEFT JOIN playlists p ON t.playlist_id = p.id
                WHERE 1=1
            """
            params = []

            if playlist_id:
                query += " AND t.playlist_id = ?"
                params.append(playlist_id)

            if status:
                query += " AND t.status = ?"
                params.append(status)

            query += " ORDER BY t.created_at DESC"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_track_status(
        self,
        track_id: int,
        status: str,
        file_path: str = None,
        file_size: int = None,
        tidal_id: int = None
    ) -> bool:
        """Update track status after download attempt."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            updates = [
                "status = ?",
                "downloaded_at = CASE WHEN ? = 'downloaded' "
                "THEN CURRENT_TIMESTAMP ELSE downloaded_at END"
            ]
            params = [status, status]

            if file_path:
                updates.append("file_path = ?")
                params.append(file_path)

            if file_size:
                updates.append("file_size = ?")
                params.append(file_size)

            if tidal_id:
                updates.append("tidal_id = ?")
                params.append(tidal_id)

            params.append(track_id)

            query = f"UPDATE tracks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            return cursor.rowcount > 0

    def get_pending_tracks(self, playlist_id: int = None) -> List[Dict]:
        """Get all pending tracks for download."""
        return self.get_tracks(playlist_id=playlist_id, status='pending')

    def delete_track(self, track_id: int) -> bool:
        """Delete a track."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
            return cursor.rowcount > 0

    # ============ Download History Methods ============

    def add_download(
        self,
        title: str,
        artist: str,
        file_path: str,
        album: str = None,
        file_size: int = None,
        quality: str = "FLAC",
        track_id: int = None
    ) -> int:
        """Record a successful download."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO downloads
                    (track_id, title, artist, album, file_path, file_size, quality)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (track_id, title, artist, album, file_path, file_size, quality))
            return cursor.lastrowid

    def get_downloads(self, limit: int = 100) -> List[Dict]:
        """Get recent downloads."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM downloads
                ORDER BY downloaded_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_download_stats(self) -> Dict:
        """Get download statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM downloads")
            total = cursor.fetchone()[0]

            cursor.execute(
                "SELECT SUM(file_size) FROM downloads WHERE file_size IS NOT NULL"
            )
            total_size = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(DISTINCT artist) FROM downloads")
            unique_artists = cursor.fetchone()[0]

            return {
                "total_downloads": total,
                "total_size_mb": total_size / (1024 * 1024) if total_size else 0,
                "unique_artists": unique_artists
            }

    # ============ Error Cache Methods ============

    def add_error(self, title: str, artist: str, error_reason: str) -> int:
        """Add or update an error in the cache."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO error_cache (title, artist, error_reason, attempts)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(title, artist) DO UPDATE SET
                    error_reason = excluded.error_reason,
                    attempts = attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (title, artist, error_reason))
            return cursor.lastrowid

    def get_errors(self, limit: int = 100) -> List[Dict]:
        """Get cached errors."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM error_cache
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_error_stats(self) -> Dict:
        """Get error statistics grouped by reason."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT error_reason, COUNT(*) as count
                FROM error_cache
                GROUP BY error_reason
                ORDER BY count DESC
            """)
            reasons = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) FROM error_cache")
            total = cursor.fetchone()[0]

            return {
                "total_errors": total,
                "by_reason": reasons
            }

    def clear_error(self, error_id: int) -> bool:
        """Remove an error from the cache."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM error_cache WHERE id = ?", (error_id,))
            return cursor.rowcount > 0

    def clear_all_errors(self) -> int:
        """Clear all errors from the cache."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM error_cache")
            return cursor.rowcount

    def is_in_error_cache(self, title: str, artist: str) -> bool:
        """Check if a track is in the error cache."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM error_cache WHERE title = ? AND artist = ?",
                (title, artist)
            )
            return cursor.fetchone() is not None

    # ============ Search Methods ============

    def search_tracks(self, query: str, limit: int = 50) -> List[Dict]:
        """Search tracks by title or artist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT t.*, p.name as playlist_name
                FROM tracks t
                LEFT JOIN playlists p ON t.playlist_id = p.id
                WHERE t.title LIKE ? OR t.artist LIKE ?
                ORDER BY t.created_at DESC
                LIMIT ?
            """, (search_term, search_term, limit))
            return [dict(row) for row in cursor.fetchall()]

    def search_downloads(self, query: str, limit: int = 50) -> List[Dict]:
        """Search downloads by title or artist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM downloads
                WHERE title LIKE ? OR artist LIKE ?
                ORDER BY downloaded_at DESC
                LIMIT ?
            """, (search_term, search_term, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ============ Statistics Methods ============

    def get_dashboard_stats(self) -> Dict:
        """Get comprehensive statistics for the dashboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Playlists count
            cursor.execute("SELECT COUNT(*) FROM playlists")
            playlists_count = cursor.fetchone()[0]

            # Tracks by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM tracks
                GROUP BY status
            """)
            tracks_by_status = {row[0]: row[1] for row in cursor.fetchall()}

            # Downloads count and size
            download_stats = self.get_download_stats()

            # Error count
            cursor.execute("SELECT COUNT(*) FROM error_cache")
            error_count = cursor.fetchone()[0]

            return {
                "playlists": playlists_count,
                "tracks_pending": tracks_by_status.get("pending", 0),
                "tracks_downloaded": tracks_by_status.get("downloaded", 0),
                "tracks_error": tracks_by_status.get("error", 0),
                "total_downloads": download_stats["total_downloads"],
                "total_size_mb": download_stats["total_size_mb"],
                "unique_artists": download_stats["unique_artists"],
                "errors_cached": error_count
            }


# Global database instance
_database: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get or create the global database instance."""
    global _database
    if _database is None:
        _database = DatabaseManager()
    return _database
