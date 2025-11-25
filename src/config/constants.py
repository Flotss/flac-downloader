"""API constants and configuration."""

from typing import List

# Tidal API servers for load balancing and redundancy
API_SERVERS: List[str] = [
    "https://kraken.squid.wtf",
    "https://triton.squid.wtf",
    "https://zeus.squid.wtf",
    "https://aether.squid.wtf",
    "https://phoenix.squid.wtf",
    "https://shiva.squid.wtf",
    "https://chaos.squid.wtf",
    "https://california.monochrome.tf",
    "https://london.monochrome.tf",
    "https://hund.qqdl.site",
    "https://katze.qqdl.site",
    "https://maus.qqdl.site",
    "https://vogel.qqdl.site",
    "https://wolf.qqdl.site",
]

# HTTP headers to mimic browser
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Origin": "https://tidal.squid.wtf",
    "Referer": "https://tidal.squid.wtf/",
}

# API timeout values
API_REQUEST_TIMEOUT = 30
API_RATE_LIMIT_WAIT = 5
API_RETRY_WAIT = 2
