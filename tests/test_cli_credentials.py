"""Tests for CLI credential storage behavior."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_cli_module(monkeypatch):
    """Load ``sonos_lastfm.cli`` with lightweight dependency stubs."""
    src_root = Path(__file__).resolve().parents[1] / "src" / "sonos_lastfm"
    cli_path = src_root / "cli.py"

    # Create package shell so relative imports resolve without importing __init__.py.
    pkg = types.ModuleType("sonos_lastfm")
    pkg.__path__ = [str(src_root)]
    monkeypatch.setitem(sys.modules, "sonos_lastfm", pkg)

    # Stub runtime dependencies used only by CLI command handlers.
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
    sonos_mod.SonosScrobbler = object
    monkeypatch.setitem(sys.modules, "sonos_lastfm.sonos_lastfm", sonos_mod)

    spec = importlib.util.spec_from_file_location("sonos_lastfm.cli", cli_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "sonos_lastfm.cli", module)
    spec.loader.exec_module(module)
    return module


def _read_env(path: Path) -> dict[str, str]:
    """Read LASTFM values from a .env-style file."""
    loaded: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.startswith("LASTFM_"):
            loaded[key[7:].lower()] = value
    return loaded


def test_save_to_env_file_merges_existing_credentials(
    tmp_path: Path, monkeypatch,
) -> None:
    """Sequential writes should preserve previously stored credentials."""
    cli = _load_cli_module(monkeypatch)
    credentials_file = tmp_path / ".env"
    monkeypatch.setattr(cli, "CREDENTIALS_FILE", credentials_file)

    cli.save_to_env_file({"username": "alice"})
    cli.save_to_env_file({"password": "secret"})
    cli.save_to_env_file({"api_key": "key-1"})
    cli.save_to_env_file({"api_secret": "sec-1"})

    assert _read_env(credentials_file) == {
        "username": "alice",
        "password": "secret",
        "api_key": "key-1",
        "api_secret": "sec-1",
    }


def test_store_credential_env_file_preserves_other_keys(
    tmp_path: Path, monkeypatch,
) -> None:
    """store_credential(env_file) should not clobber previous keys."""
    cli = _load_cli_module(monkeypatch)
    credentials_file = tmp_path / ".env"
    monkeypatch.setattr(cli, "CREDENTIALS_FILE", credentials_file)

    cli.store_credential("username", "alice", "env_file")
    cli.store_credential("password", "secret", "env_file")

    assert _read_env(credentials_file) == {
        "username": "alice",
        "password": "secret",
    }


def test_delete_credential_removes_only_selected_key(
    tmp_path: Path, monkeypatch,
) -> None:
    """Deleting one key should keep other credentials untouched."""
    cli = _load_cli_module(monkeypatch)
    credentials_file = tmp_path / ".env"
    monkeypatch.setattr(cli, "CREDENTIALS_FILE", credentials_file)
    monkeypatch.setattr(cli, "HAS_KEYRING", False)
    monkeypatch.setattr(cli, "keyring", None)

    cli.save_to_env_file({"username": "alice", "password": "secret"})
    cli.delete_credential("password")

    assert _read_env(credentials_file) == {"username": "alice"}
