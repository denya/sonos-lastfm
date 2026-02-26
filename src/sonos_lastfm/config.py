# Copyright (c) 2025 Denis Moskalets
# Licensed under the MIT License.

"""Configuration helpers for Sonos Last.fm scrobbler."""

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


MIN_THRESHOLD_PERCENT: Final[float] = 0.0
MAX_THRESHOLD_PERCENT: Final[float] = 100.0
DEFAULT_THRESHOLD_PERCENT: Final[float] = 25.0


def validate_config() -> list[str] | None:
    """Validate required environment variables.

    Returns:
        List of missing variables if any, None if all required vars are present
    """
    required_vars = [
        "LASTFM_USERNAME",
        "LASTFM_PASSWORD",
        "LASTFM_API_KEY",
        "LASTFM_API_SECRET",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    return missing_vars or None


def get_config() -> dict[str, object]:
    """Get configuration values, validating them first.

    Raises:
        ValueError: If required environment variables are missing

    Returns:
        A dictionary containing validated configuration settings.
    """
    if missing := validate_config():
        missing_vars = ", ".join(missing)
        error_message = (
            "Missing required environment variables: "
            f"{missing_vars}\nPlease set them in your .env file"
        )
        raise ValueError(error_message)

    return {
        # Last.fm API credentials
        "LASTFM_USERNAME": os.getenv("LASTFM_USERNAME"),
        "LASTFM_PASSWORD": os.getenv("LASTFM_PASSWORD"),
        "LASTFM_API_KEY": os.getenv("LASTFM_API_KEY"),
        "LASTFM_API_SECRET": os.getenv("LASTFM_API_SECRET"),
        # Scrobbling settings
        "SCROBBLE_INTERVAL": int(os.getenv("SCROBBLE_INTERVAL", "1")),  # seconds
        "SPEAKER_REDISCOVERY_INTERVAL": int(
            os.getenv("SPEAKER_REDISCOVERY_INTERVAL", "10"),
        ),  # seconds
        # Get and validate scrobble threshold percentage
        "SCROBBLE_THRESHOLD_PERCENT": min(
            max(
                float(os.getenv("SCROBBLE_THRESHOLD_PERCENT") or "25"),
                MIN_THRESHOLD_PERCENT,
            ),
            MAX_THRESHOLD_PERCENT,
        ),
        # Data storage paths
        "DATA_DIR": Path("./data"),
    }


# Export config values but don't validate at import time
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")
LASTFM_PASSWORD = os.getenv("LASTFM_PASSWORD")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET")

# Scrobbling settings
SCROBBLE_INTERVAL = int(os.getenv("SCROBBLE_INTERVAL", "1"))  # seconds
SPEAKER_REDISCOVERY_INTERVAL = int(
    os.getenv("SPEAKER_REDISCOVERY_INTERVAL", "10"),
)  # seconds

# Get and validate scrobble threshold percentage
SCROBBLE_THRESHOLD_PERCENT = float(
    os.getenv("SCROBBLE_THRESHOLD_PERCENT") or str(DEFAULT_THRESHOLD_PERCENT),
)
if not MIN_THRESHOLD_PERCENT <= SCROBBLE_THRESHOLD_PERCENT <= MAX_THRESHOLD_PERCENT:
    SCROBBLE_THRESHOLD_PERCENT = DEFAULT_THRESHOLD_PERCENT

# Data storage paths
DATA_DIR = Path("./data")
LAST_SCROBBLED_FILE = DATA_DIR / "last_scrobbled.json"
CURRENTLY_PLAYING_FILE = DATA_DIR / "currently_playing.json"
