# 🚀 Getting Started Guide

## Step 1: Verify Structure

```bash
cd /home/flotss/Projects/flac-downloader
ls -la
```

Expected files:

- `src/` - Application code
- `tests/` - Test suite
- `data/` - Runtime data directory
- `README.md` - Quick start
- `ARCHITECTURE.md` - Detailed architecture
- `PROJECT_SUMMARY.md` - Refactoring summary
- `pyproject.toml` - Project config
- `requirements.txt` - Dependencies
- `run.py` - Entry point

## Step 2: Create Virtual Environment

### Option A: Using setup script (Recommended)

```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
```

### Option B: Manual setup

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Configure Credentials

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env
```

Required in `.env`:

```
SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here
SPOTIFY_PLAYLIST_URL=https://open.spotify.com/playlist/...
DOWNLOAD_FOLDER=/path/to/music/folder
```

Get credentials from: https://developer.spotify.com/dashboard

## Step 4: Test Installation

```bash
# Run tests
pytest tests/ -v

# Check imports
python -c "from src.main import main; print('✅ Imports working')"
```

## Step 5: Run Downloader

```bash
python run.py
```

or with make:

```bash
make run
```

## Useful Commands

```bash
make install           # Install dependencies
make dev              # Install with dev tools
make test             # Run tests
make lint             # Check code quality
make format           # Auto-format code
make clean            # Remove build artifacts
make help             # Show all commands
```

## Troubleshooting

### "Spotify credentials not configured"

- ✅ Check `.env` file exists
- ✅ Verify `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are set
- ✅ Restart Python after editing `.env`

### "No module named 'src'"

- ✅ Run from project root: `cd /home/flotss/Projects/flac-downloader`
- ✅ Check virtual environment is activated
- ✅ Reinstall: `pip install -r requirements.txt`

### "Connection refused"

- ✅ Check internet connection
- ✅ API servers may be down (try later)
- ✅ Check rate limiting (automatic backoff included)

### Files re-downloading

- ✅ Clear cache: `rm data/tmp_spotify_playlist.json`
- ✅ Or wait 1 hour for cache to expire

## Project Organization

### For Development

1. Make changes in `src/`
2. Run tests: `make test`
3. Format code: `make format`
4. Check quality: `make lint`

### For Usage

1. Configure `.env`
2. Run: `python run.py`
3. Check logs: `data/download_*.log`
4. Review failures: `data/download_log.csv`

## Architecture Overview

```
User runs → run.py
    ↓
DownloadSession.run()
    ↓
SpotifyService → Get playlist
    ↓
Downloader → Check duplicates, orchestrate
    ↓
TidalAPI → Search & download
    ↓
MetadataManager → Add FLAC tags
    ↓
CSV Logger → Log failures
```

## Next Steps

1. ✅ Install & configure
2. ✅ Run first download
3. ✅ Review logs in `data/`
4. ✅ Check downloaded files
5. ✅ Explore code structure
6. ✅ Modify for your needs

## Documentation

- **README.md** - Quick start & features
- **ARCHITECTURE.md** - Detailed design
- **PROJECT_SUMMARY.md** - Refactoring overview
- **Inline docstrings** - Code documentation

## Support

### Checking code

```bash
# View project structure
ls -R src/

# Check specific module
cat src/services/downloader.py

# Run with verbose logging
LOG_LEVEL=DEBUG python run.py
```

### Testing changes

```bash
# After editing code
pytest tests/ -v

# Run specific test
pytest tests/test_utils.py::TestTrackModel -v

# With coverage
pytest tests/ --cov=src
```

## Performance Notes

- First run: ~1-2 minutes for setup
- Subsequent runs: ~30 seconds per track
- Playlist cached 1 hour
- Automatic retry on failures

## Examples

### Download specific playlist

```bash
# Edit .env
SPOTIFY_PLAYLIST_URL=https://open.spotify.com/playlist/YOUR_ID

# Run
python run.py
```

### Download to custom folder

```bash
# Edit .env
DOWNLOAD_FOLDER=/home/user/MyMusic

# Run
python run.py
```

### Retry failed downloads

```bash
# Failed songs in data/download_log.csv
# Just run again - it will retry
python run.py
```

---

**Everything is ready! Start with `python run.py`** 🎶
