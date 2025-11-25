# FLAC Downloader

A high-performance Python application to download Spotify playlist tracks in FLAC quality using the Tidal API.

## Features

- 🎵 **Spotify Integration**: Automatically fetch tracks from any Spotify playlist
- 🔊 **FLAC Quality**: Downloads in high-quality FLAC format via reverse-engineered Tidal API
- ⚡ **Multiple API Servers**: Automatic failover and load balancing across 14+ servers
- 🔄 **Automatic Retries**: Smart retry logic with exponential backoff
- 📊 **Progress Tracking**: Real-time download progress and detailed logging
- 💾 **Metadata Tags**: Automatically adds FLAC tags with track information
- 📝 **CSV Logging**: Records failed downloads for retry attempts
- 🎯 **Smart Duplicate Detection**: Avoids re-downloading tracks already present

## Installation

### Prerequisites

- Python 3.8+
- pip or poetry

### Setup

1. Clone the repository:

```bash
git clone <repository>
cd flac-downloader
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

Or with modern Python packaging:

```bash
pip install -e .
```

3. Configure credentials:

```bash
cp .env.example .env
```

4. Get Spotify credentials:
   - Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create an application to get `CLIENT_ID` and `CLIENT_SECRET`
   - Update `.env` with your credentials

## Usage

### Basic Usage

```bash
python run.py
```

### Configuration

Edit `.env` file or set environment variables:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_PLAYLIST_URL=https://open.spotify.com/playlist/...
DOWNLOAD_FOLDER=/path/to/music
DOWNLOAD_TIMEOUT=120
RETRY_MAX_COUNT=3
```

## Project Structure

```
flac-downloader/
├── src/
│   ├── config/           # Configuration (settings, constants)
│   ├── core/             # Core models and exceptions
│   ├── services/         # Business logic (API, Spotify, Downloader)
│   ├── utils/            # Utility functions
│   └── main.py           # Main entry point
├── data/                 # Runtime data (logs, cache, CSV logs)
├── tests/                # Unit tests
├── pyproject.toml        # Python project configuration
├── requirements.txt      # Dependencies
├── .env.example          # Environment variables template
└── run.py               # Entry point script
```

## Architecture

The project follows clean architecture principles:

- **Config Layer**: Centralized settings and constants
- **Core Layer**: Domain models and exceptions
- **Services Layer**: Business logic (API clients, downloaders)
- **Utils Layer**: Reusable utility functions
- **Main**: Orchestration and session management

## Logging

Logs are saved to `data/download_YYYYMMDD_HHMMSS.log` with:

- Colored console output
- Detailed debugging information
- File rotation support

## Error Handling

Failed downloads are recorded in `data/download_log.csv` and can be retried by running the script again.

## Development

### Running Tests

```bash
pytest
pytest --cov=src          # With coverage
```

### Code Style

```bash
black src/
isort src/
flake8 src/
mypy src/
```

## Limitations

- Requires valid Spotify credentials
- Tidal API endpoints may change (reverse-engineered)
- Subject to rate limiting on API servers

## License

MIT License - see LICENSE file for details

## Troubleshooting

### "Spotify credentials not configured"

- Ensure `.env` has `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`

### "No response from /song/"

- API servers may be temporarily unavailable
- Retry: the script has automatic retry logic

### Files already downloaded but re-downloading

- Clear `data/tmp_spotify_playlist.json` to refresh playlist cache
- Or wait 1 hour for cache to expire

## Contributing

Contributions welcome! Please follow the existing code style and add tests for new features.

## Support

For issues or questions, create an issue on the GitHub repository.
