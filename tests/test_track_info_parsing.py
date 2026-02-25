"""Tests for track info parsing and return contracts."""

from __future__ import annotations

import importlib.util
import logging
import sys
import types
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
        "sonos_lastfm.sonos_lastfm", module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "sonos_lastfm.sonos_lastfm", module)
    spec.loader.exec_module(module)
    return module


def test_update_track_info_returns_empty_dict_when_duration_missing(monkeypatch) -> None:
    """Duration NOT_IMPLEMENTED should produce an empty dict."""
    module = _load_sonos_module(monkeypatch)

    class FakeSpeaker:
        player_name = "Kitchen"

        @staticmethod
        def get_current_track_info() -> dict[str, str]:
            return {
                "artist": "A",
                "title": "T",
                "album": "B",
                "duration": "NOT_IMPLEMENTED",
                "position": "0:10",
            }

        @staticmethod
        def get_current_transport_info() -> dict[str, str]:
            return {"current_transport_state": "PLAYING"}

    assert module.SonosScrobbler.update_track_info(FakeSpeaker()) == {}


def test_update_track_info_returns_empty_dict_when_position_missing(monkeypatch) -> None:
    """Position NOT_IMPLEMENTED should produce an empty dict."""
    module = _load_sonos_module(monkeypatch)

    class FakeSpeaker:
        player_name = "Kitchen"

        @staticmethod
        def get_current_track_info() -> dict[str, str]:
            return {
                "artist": "A",
                "title": "T",
                "album": "B",
                "duration": "4:00",
                "position": "NOT_IMPLEMENTED",
            }

        @staticmethod
        def get_current_transport_info() -> dict[str, str]:
            return {"current_transport_state": "PLAYING"}

    assert module.SonosScrobbler.update_track_info(FakeSpeaker()) == {}


def test_update_track_info_parses_hms_values(monkeypatch) -> None:
    """H:MM:SS values should be converted to integer seconds."""
    module = _load_sonos_module(monkeypatch)

    class FakeSpeaker:
        player_name = "Kitchen"

        @staticmethod
        def get_current_track_info() -> dict[str, str]:
            return {
                "artist": "Artist",
                "title": "Title",
                "album": "Album",
                "duration": "1:02:03",
                "position": "0:05:06",
            }

        @staticmethod
        def get_current_transport_info() -> dict[str, str]:
            return {"current_transport_state": "PLAYING"}

    assert module.SonosScrobbler.update_track_info(FakeSpeaker()) == {
        "artist": "Artist",
        "title": "Title",
        "album": "Album",
        "duration": 3723,
        "position": 306,
        "state": "PLAYING",
    }
