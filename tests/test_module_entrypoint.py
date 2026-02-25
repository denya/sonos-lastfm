"""Tests for ``python -m sonos_lastfm`` entrypoint behavior."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def test_main_delegates_to_cli_main(monkeypatch) -> None:
    """Package module entrypoint should invoke CLI entrypoint."""
    src_root = Path(__file__).resolve().parents[1] / "src" / "sonos_lastfm"
    module_path = src_root / "__main__.py"

    pkg = types.ModuleType("sonos_lastfm")
    pkg.__path__ = [str(src_root)]
    monkeypatch.setitem(sys.modules, "sonos_lastfm", pkg)

    called = {"value": False}

    cli_mod = types.ModuleType("sonos_lastfm.cli")

    def fake_main() -> None:
        called["value"] = True

    cli_mod.main = fake_main
    monkeypatch.setitem(sys.modules, "sonos_lastfm.cli", cli_mod)

    spec = importlib.util.spec_from_file_location("sonos_lastfm.__main__", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "sonos_lastfm.__main__", module)
    spec.loader.exec_module(module)

    module.main()
    assert called["value"] is True
