"""Tests for core scrobble decision logic."""

from __future__ import annotations

import importlib.util
import logging
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _load_sonos_module(monkeypatch):
    """Load ``sonos_lastfm.sonos_lastfm`` with test stubs."""
    src_root = Path(__file__).resolve().parents[1] / "src" / "sonos_lastfm"
    module_path = src_root / "sonos_lastfm.py"

    pkg = types.ModuleType("sonos_lastfm")
    pkg.__path__ = [str(src_root)]
    monkeypatch.setitem(sys.modules, "sonos_lastfm", pkg)

    pylast_mod = types.ModuleType("pylast")
    pylast_mod.PylastError = Exception
    pylast_mod.LastFMNetwork = object
    pylast_mod.md5 = lambda value: value
    monkeypatch.setitem(sys.modules, "pylast", pylast_mod)

    soco_mod = types.ModuleType("soco")
    soco_mod.discover = lambda: []
    soco_mod.SoCo = object
    monkeypatch.setitem(sys.modules, "soco", soco_mod)

    soco_exceptions_mod = types.ModuleType("soco.exceptions")

    class SoCoException(Exception):
        pass

    soco_exceptions_mod.SoCoException = SoCoException
    monkeypatch.setitem(sys.modules, "soco.exceptions", soco_exceptions_mod)

    config_mod = types.ModuleType("sonos_lastfm.config")
    config_mod.get_config = lambda: {
        "DATA_DIR": Path("./data"),
        "LASTFM_API_KEY": "key",
        "LASTFM_API_SECRET": "secret",
        "LASTFM_USERNAME": "user",
        "LASTFM_PASSWORD": "pass",
        "SCROBBLE_INTERVAL": 1,
        "SPEAKER_REDISCOVERY_INTERVAL": 10,
        "SCROBBLE_THRESHOLD_PERCENT": 25.0,
    }
    monkeypatch.setitem(sys.modules, "sonos_lastfm.config", config_mod)

    utils_mod = types.ModuleType("sonos_lastfm.utils")
    utils_mod.custom_print = lambda *args, **kwargs: None  # noqa: ARG005
    utils_mod.logger = logging.getLogger("test-sonos")
    utils_mod.update_all_progress_displays = lambda *args, **kwargs: None  # noqa: ARG005
    monkeypatch.setitem(sys.modules, "sonos_lastfm.utils", utils_mod)

    spec = importlib.util.spec_from_file_location(
        "sonos_lastfm.sonos_lastfm",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "sonos_lastfm.sonos_lastfm", module)
    spec.loader.exec_module(module)
    return module


def _make_scrobbler(
    module, *, threshold=25.0, last_scrobbled=None, currently_playing=None
):
    """Create a SonosScrobbler without running __init__."""
    scrobbler = object.__new__(module.SonosScrobbler)
    scrobbler.scrobble_threshold_percent = threshold
    scrobbler.last_scrobbled = last_scrobbled or {}
    scrobbler.currently_playing = currently_playing or {}
    return scrobbler


def test_should_scrobble_true_past_threshold(monkeypatch) -> None:
    """Position at 30%, threshold 25% -> True."""
    module = _load_sonos_module(monkeypatch)
    scrobbler = _make_scrobbler(
        module,
        threshold=25.0,
        currently_playing={
            "192.168.1.1": {"position": 300, "duration": 1000},
        },
    )
    track_info = {"artist": "Artist", "title": "Title"}

    assert scrobbler.should_scrobble(track_info, "192.168.1.1") is True


def test_should_scrobble_true_past_4_minutes(monkeypatch) -> None:
    """Position 241s, duration 1000s, under threshold -> True (4-min rule)."""
    module = _load_sonos_module(monkeypatch)
    scrobbler = _make_scrobbler(
        module,
        threshold=25.0,
        currently_playing={
            "192.168.1.1": {"position": 241, "duration": 1000},
        },
    )
    track_info = {"artist": "Artist", "title": "Title"}

    # 241/1000 = 24.1% < 25% threshold, but 241 >= 240 (SCROBBLE_MIN_TIME)
    assert scrobbler.should_scrobble(track_info, "192.168.1.1") is True


def test_should_scrobble_false_below_threshold(monkeypatch) -> None:
    """Position 10%, under 4 min -> False."""
    module = _load_sonos_module(monkeypatch)
    scrobbler = _make_scrobbler(
        module,
        threshold=25.0,
        currently_playing={
            "192.168.1.1": {"position": 60, "duration": 600},
        },
    )
    track_info = {"artist": "Artist", "title": "Title"}

    # 60/600 = 10% < 25%, 60 < 240
    assert scrobbler.should_scrobble(track_info, "192.168.1.1") is False


def test_should_scrobble_false_recently_scrobbled(monkeypatch) -> None:
    """Same track scrobbled 5 min ago -> False."""
    module = _load_sonos_module(monkeypatch)
    five_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    scrobbler = _make_scrobbler(
        module,
        threshold=25.0,
        last_scrobbled={"Artist-Title": five_min_ago},
        currently_playing={
            "192.168.1.1": {"position": 300, "duration": 1000},
        },
    )
    track_info = {"artist": "Artist", "title": "Title"}

    # Would pass threshold, but was scrobbled 5 min ago (< 30 min window)
    assert scrobbler.should_scrobble(track_info, "192.168.1.1") is False
