# Architecture Documentation

## Overview

FLAC Downloader is designed following **Clean Architecture** principles, ensuring separation of concerns, maintainability, and testability.

## Layer Structure

### 1. **Configuration Layer** (`src/config/`)

**Responsibility**: Centralized management of settings and constants.

- `settings.py`: Environment-based configuration (paths, credentials, timeouts)
- `constants.py`: Static constants (API servers, HTTP headers)

**Benefits**:

- Easy environment variable management
- Testable configuration
- Single source of truth

### 2. **Core Layer** (`src/core/`)

**Responsibility**: Domain models, exceptions, and logging infrastructure.

- `models.py`: Domain entities (`Track`, `StreamInfo`)
- `exceptions.py`: Custom exception hierarchy
- `logging.py`: Centralized logging with colors

**Design Patterns**:

- Dataclasses for immutable domain objects
- Exception hierarchy for precise error handling

### 3. **Services Layer** (`src/services/`)

**Responsibility**: Business logic and external service integration.

#### Key Services:

**`TidalAPI`** (`tidal_api.py`)

- HTTP requests with automatic server rotation
- Search functionality
- Stream URL extraction
- Download management
- Statistics tracking

**`SpotifyService`** (`spotify_service.py`)

- Spotify API integration
- Playlist fetching with pagination
- Response caching

**`Downloader`** (`downloader.py`)

- Orchestrates download workflow
- Track matching logic (two-strategy approach)
- Duplicate detection
- Retry management

**`MetadataManager`** (`metadata.py`)

- FLAC tag management
- Track ID extraction
- Metadata validation

### 4. **Utilities Layer** (`src/utils/`)

**Responsibility**: Reusable utility functions without state.

- `text.py`: String normalization, filename sanitization
- `file_manager.py`: File system operations
- `csv_logger.py`: CSV logging for failed downloads

**Design Principle**: Pure functions, no side effects beyond their scope.

### 5. **Main/Orchestration** (`src/main.py`)

**Responsibility**: Session management and workflow orchestration.

`DownloadSession` class:

- Initializes services
- Manages complete download workflow
- Handles errors and cleanup
- Generates reports

## Data Flow

```
Spotify Playlist URL
        ↓
SpotifyService.get_playlist_tracks()
        ↓
List of (title, artist) tuples
        ↓
Downloader.is_track_downloaded() → Filter existing files
        ↓
Filtered tracks list
        ↓
For each track:
    Downloader.download_song()
        ↓
    TidalAPI.get_song_direct() OR search + match
        ↓
    StreamInfo
        ↓
    TidalAPI.download_track()
        ↓
    MetadataManager.add_track_metadata()
        ↓
    Success/Failure → CSV Log
```

## Key Design Patterns

### 1. **Dependency Injection**

Services receive their dependencies via constructor:

```python
downloader = Downloader(api=TidalAPI())
```

### 2. **Strategy Pattern**

Download uses two strategies:

1. Direct `/song/` endpoint (fast)
2. Search + stream separately (fallback)

### 3. **Retry with Backoff**

API requests automatically retry with:

- Server rotation
- Exponential backoff
- Maximum retry limits

### 4. **Caching**

Spotify playlist cached for 1 hour to reduce API calls

### 5. **Error Recovery**

- Automatic retry for transient failures
- CSV logging for permanent failures
- Graceful degradation

## Testing Strategy

### Unit Tests (`tests/`)

**Structure**:

- `test_utils.py`: Text and file utilities
- `conftest.py`: Pytest fixtures

**Approach**:

- Mock external services
- Test pure functions
- Verify error handling

## Configuration Management

### Environment Variables

Load from `.env` or set in OS:

```bash
export SPOTIFY_CLIENT_ID=...
export SPOTIFY_CLIENT_SECRET=...
```

### Hierarchy

1. Environment variables (highest priority)
2. `.env` file
3. Hardcoded defaults (development)

## Error Handling

### Exception Hierarchy

```
DownloaderException (base)
├── SongNotFoundError
├── DownloadError
└── APIError
```

### Logging Strategy

- **DEBUG**: Detailed information for troubleshooting
- **INFO**: Progress and important events
- **WARNING**: Retryable errors
- **ERROR**: Non-retryable failures
- **CRITICAL**: Fatal errors

Logs written to both console (colored) and file (plain text).

## Performance Considerations

1. **API Load Balancing**: 14+ servers reduce single-point failures
2. **Caching**: Playlist cached 1 hour to avoid re-fetching
3. **Progress Display**: Real-time download progress bars
4. **Batch Operations**: Process multiple files efficiently

## Extensibility

### Adding New Features

**Example: Add YouTube support**

```python
# Create new service
class YouTubeService:
    def search_track(self, query):
        # Implementation
        pass

# Update Downloader
class Downloader:
    def download_song(self, title, artist, source="tidal"):
        if source == "youtube":
            return self._download_youtube(title, artist)
```

### Adding New API Servers

Update `src/config/constants.py`:

```python
API_SERVERS = [
    "...",
    "https://new-server.com",
]
```

## Maintenance Guidelines

1. **Keep services independent**: Each service handles one responsibility
2. **Use type hints**: Help with IDE support and documentation
3. **Test edge cases**: Empty results, timeouts, malformed responses
4. **Document assumptions**: Comment on why, not what
5. **Log appropriately**: Use right level for each message

## Security Considerations

1. **Credentials**: Load from environment, never hardcode
2. **Rate Limiting**: Respect API limits with backoff
3. **Input Validation**: Sanitize filenames and search queries
4. **Error Messages**: Don't expose sensitive data in logs

## Future Improvements

1. **Database Support**: Store download history
2. **Web UI**: Browser-based configuration and monitoring
3. **Batch Processing**: Queue management for large playlists
4. **Quality Selection**: Let users choose audio quality
5. **Format Support**: Add formats beyond FLAC
