"""Tests for configuration validation and threshold clamping."""

from __future__ import annotations

from sonos_lastfm.config import get_config, validate_config


def test_validate_config_returns_none_when_all_set(monkeypatch) -> None:
    """All 4 env vars present -> None."""
    monkeypatch.setenv("LASTFM_USERNAME", "user")
    monkeypatch.setenv("LASTFM_PASSWORD", "pass")
    monkeypatch.setenv("LASTFM_API_KEY", "key")
    monkeypatch.setenv("LASTFM_API_SECRET", "secret")

    assert validate_config() is None


def test_validate_config_returns_missing_vars(monkeypatch) -> None:
    """2 missing -> returns list of 2."""
    monkeypatch.setenv("LASTFM_USERNAME", "user")
    monkeypatch.setenv("LASTFM_PASSWORD", "pass")
    monkeypatch.delenv("LASTFM_API_KEY", raising=False)
    monkeypatch.delenv("LASTFM_API_SECRET", raising=False)

    result = validate_config()
    assert result is not None
    assert len(result) == 2
    assert "LASTFM_API_KEY" in result
    assert "LASTFM_API_SECRET" in result


def test_get_config_clamps_threshold(monkeypatch) -> None:
    """Set threshold to 150 -> clamped to 100.0."""
    monkeypatch.setenv("LASTFM_USERNAME", "user")
    monkeypatch.setenv("LASTFM_PASSWORD", "pass")
    monkeypatch.setenv("LASTFM_API_KEY", "key")
    monkeypatch.setenv("LASTFM_API_SECRET", "secret")
    monkeypatch.setenv("SCROBBLE_THRESHOLD_PERCENT", "150")

    config = get_config()
    assert config["SCROBBLE_THRESHOLD_PERCENT"] == 100.0
