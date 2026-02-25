# Copyright (c) 2025 Denis Moskalets
# Licensed under the MIT License.

"""Main entry point for the sonos_lastfm package."""

from .cli import main as cli_main


def main() -> None:
    """Run the Sonos Last.fm CLI."""
    cli_main()


if __name__ == "__main__":
    main()
