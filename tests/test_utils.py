"""Tests for progress bar rendering."""

from __future__ import annotations

from sonos_lastfm.utils import create_progress_bar


def test_create_progress_bar_zero_total() -> None:
    """total=0 -> empty bar with 0%."""
    result = create_progress_bar(current=0, total=0, threshold=0)
    assert result == "[" + " " * 50 + "] 0%"


def test_create_progress_bar_shows_percentage() -> None:
    """position=50, total=100 -> bar contains '50%'."""
    result = create_progress_bar(current=50, total=100, threshold=25)
    assert "50%" in result
