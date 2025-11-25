#!/usr/bin/env python3
"""Main entry point - run the FLAC downloader."""

import sys
import os

# Add src to path for proper imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

from src.main import main

if __name__ == "__main__":
    main()
