# Copyright (c) 2025 Denis Moskalets
# Licensed under the MIT License.

"""Sonos Last.fm scrobbler package."""

from .cli import main
from .sonos_lastfm import SonosScrobbler

__version__ = "0.1.8"
__all__ = ["SonosScrobbler", "main"]
