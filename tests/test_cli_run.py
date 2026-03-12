"""Tests for CLI ``run`` command error paths and credential handling."""

from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _load_cli_module(monkeypatch):
    """Load ``sonos_lastfm.cli`` with lightweight dependency stubs."""
    src_root = Path(__file__).resolve().parents[1] / "src" / "sonos_lastfm"
    cli_path = src_root / "cli.py"

    pkg = types.ModuleType("sonos_lastfm")
    pkg.__path__ = [str(src_root)]
    monkeypatch.setitem(sys.modules, "sonos_lastfm", pkg)

    typer_mod = types.ModuleType("typer")

    class DummyTyper:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            pass

        def command(self, *args, **kwargs):  # noqa: ANN002, ANN003
            def decorator(func):
                return func

            return decorator

    class DummyExit(Exception):
        def __init__(self, code: int = 1):
            self.code = code

    def dummy_option(default=None, *args, **kwargs):  # noqa: ANN002, ANN003
        return default

    typer_mod.Typer = DummyTyper
    typer_mod.Option = dummy_option
    typer_mod.Exit = DummyExit
    monkeypatch.setitem(sys.modules, "typer", typer_mod)

    rich_mod = types.ModuleType("rich")
    rich_mod.print = lambda *args, **kwargs: None  # noqa: ARG005
    monkeypatch.setitem(sys.modules, "rich", rich_mod)

    rich_console_mod = types.ModuleType("rich.console")

    class DummyConsole:
        def status(self, *args, **kwargs):  # noqa: ANN002, ANN003
            class _Ctx:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, exc_type, exc, tb):  # noqa: ANN001, ANN201
                    return False

                def update(self_inner, *args, **kwargs):  # noqa: ANN002, ANN003
                    return None

            return _Ctx()

        def print(self, *args, **kwargs):  # noqa: ANN002, ANN003
            return None

    rich_console_mod.Console = DummyConsole
    monkeypatch.setitem(sys.modules, "rich.console", rich_console_mod)

    rich_prompt_mod = types.ModuleType("rich.prompt")

    class DummyConfirm:
        @staticmethod
        def ask(*args, **kwargs):  # noqa: ANN002, ANN003
            return False

    class DummyPrompt:
        @staticmethod
        def ask(*args, **kwargs):  # noqa: ANN002, ANN003
            return ""

    rich_prompt_mod.Confirm = DummyConfirm
    rich_prompt_mod.Prompt = DummyPrompt
    monkeypatch.setitem(sys.modules, "rich.prompt", rich_prompt_mod)

    rich_table_mod = types.ModuleType("rich.table")

    class DummyTable:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            pass

        def add_column(self, *args, **kwargs):  # noqa: ANN002, ANN003
            return None

        def add_row(self, *args, **kwargs):  # noqa: ANN002, ANN003
            return None

    rich_table_mod.Table = DummyTable
    monkeypatch.setitem(sys.modules, "rich.table", rich_table_mod)

    pylast_mod = types.ModuleType("pylast")
    pylast_mod.PylastError = Exception
    pylast_mod.LastFMNetwork = object
    pylast_mod.md5 = lambda value: value
    monkeypatch.setitem(sys.modules, "pylast", pylast_mod)

    sonos_mod = types.ModuleType("sonos_lastfm.sonos_lastfm")
    sonos_mod.SonosScrobbler = MagicMock
    monkeypatch.setitem(sys.modules, "sonos_lastfm.sonos_lastfm", sonos_mod)

    spec = importlib.util.spec_from_file_location("sonos_lastfm.cli", cli_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "sonos_lastfm.cli", module)
    spec.loader.exec_module(module)
    return module


def test_run_missing_all_credentials_raises_exit(monkeypatch) -> None:
    """No creds set, Confirm.ask returns False -> typer.Exit raised."""
    cli = _load_cli_module(monkeypatch)

    # Clear all credential env vars
    for var in (
        "LASTFM_USERNAME",
        "LASTFM_PASSWORD",
        "LASTFM_API_KEY",
        "LASTFM_API_SECRET",
    ):
        monkeypatch.delenv(var, raising=False)

    # Ensure no stored credentials are found
    monkeypatch.setattr(cli, "CREDENTIALS_FILE", Path("/nonexistent/.env"))
    monkeypatch.setattr(cli, "HAS_KEYRING", False)
    monkeypatch.setattr(cli, "keyring", None)

    with pytest.raises(cli.typer.Exit):
        cli.run(
            setup=False,
            daemon=False,
            username=None,
            password=None,
            api_key=None,
            api_secret=None,
            scrobble_interval=1,
            rediscovery_interval=10,
            threshold=25.0,
        )


def test_run_with_all_credentials_sets_env_vars(monkeypatch) -> None:
    """All 4 creds provided as args -> os.environ is set correctly."""
    cli = _load_cli_module(monkeypatch)

    # Clear any existing credential env vars
    for var in (
        "LASTFM_USERNAME",
        "LASTFM_PASSWORD",
        "LASTFM_API_KEY",
        "LASTFM_API_SECRET",
    ):
        monkeypatch.delenv(var, raising=False)

    # Mock SonosScrobbler to prevent actual network calls
    mock_scrobbler = MagicMock()
    monkeypatch.setattr(cli, "SonosScrobbler", lambda: mock_scrobbler)

    cli.run(
        setup=False,
        daemon=False,
        username="testuser",
        password="testpass",
        api_key="testkey",
        api_secret="testsecret",
        scrobble_interval=5,
        rediscovery_interval=20,
        threshold=50.0,
    )

    assert os.environ["LASTFM_USERNAME"] == "testuser"
    assert os.environ["LASTFM_PASSWORD"] == "testpass"
    assert os.environ["LASTFM_API_KEY"] == "testkey"
    assert os.environ["LASTFM_API_SECRET"] == "testsecret"
    assert os.environ["SCROBBLE_INTERVAL"] == "5"
    assert os.environ["SPEAKER_REDISCOVERY_INTERVAL"] == "20"
    assert os.environ["SCROBBLE_THRESHOLD_PERCENT"] == "50.0"

    mock_scrobbler.run.assert_called_once_with(daemon=False)
