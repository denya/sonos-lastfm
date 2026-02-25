# Copyright (c) 2025 Denis Moskalets
# Licensed under the MIT License.

"""Command line interface for Sonos Last.fm scrobbler."""

from __future__ import annotations

import os
import traceback
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

import pylast  # type: ignore[import-untyped]
import rich
import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .sonos_lastfm import SonosScrobbler

# Make keyring truly optional
KeyringError: type[Exception] = Exception
try:
    import keyring
except ImportError as exc:
    keyring = None  # type: ignore[assignment]
    HAS_KEYRING = False
    KEYRING_ERROR = str(exc)
else:
    HAS_KEYRING = True
    KEYRING_ERROR = ""
    try:
        from keyring.errors import KeyringError as _KeyringError
    except ImportError:
        pass
    else:
        KeyringError = _KeyringError

# Create Typer app instance
app = typer.Typer(
    name="sonos-lastfm",
    help="Scrobble your Sonos plays to Last.fm",
    add_completion=False,
    no_args_is_help=True,  # Show help when no command is provided
)

# Constants
APP_NAME = "sonos-lastfm"
CONFIG_DIR = Path.home() / ".sonos_lastfm"
CREDENTIAL_KEYS = ["username", "password", "api_key", "api_secret"]

# Storage options
StorageType = Literal["env_file", "keyring"]

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Create a simple file-based storage
CREDENTIALS_FILE = CONFIG_DIR / ".env"


def save_to_env_file(credentials: dict[str, str], merge: bool = True) -> None:
    """Save credentials to .env file in config directory.

    Args:
        credentials: Dictionary of credentials to save
        merge: Whether to merge with existing file content before writing
    """
    try:
        merged_credentials = load_from_env_file() if merge else {}
        merged_credentials.update(credentials)
        with CREDENTIALS_FILE.open("w", encoding="utf-8") as f:
            for key, value in merged_credentials.items():
                f.write(f"LASTFM_{key.upper()}={value}\n")
        rich.print(f"[green]✓[/green] Credentials saved to {CREDENTIALS_FILE}")
    except OSError as exc:
        error_message = (
            "[red]Error:[/red] Could not save credentials to "
            f"{CREDENTIALS_FILE}: {exc}"
        )
        rich.print(error_message)


def load_from_env_file() -> dict[str, str]:
    """Load credentials from .env file.

    Returns:
        Dictionary of credentials
    """
    credentials: dict[str, str] = {}
    if not CREDENTIALS_FILE.exists():
        return credentials

    try:
        with CREDENTIALS_FILE.open(encoding="utf-8") as file_handle:
            for line in file_handle:
                if "=" not in line:
                    continue
                env_key, value = line.strip().split("=", 1)
                if env_key.startswith("LASTFM_"):
                    credentials[env_key[7:].lower()] = value
    except OSError:
        return credentials

    return credentials


def get_stored_credential(key: str) -> str | None:
    """Get a credential from available storage methods.

    Args:
        key: The key to retrieve

    Returns:
        The stored credential or None if not found
    """
    # First try environment variable
    env_key = f"LASTFM_{key.upper()}"
    if value := os.getenv(env_key):
        return value

    # Then try keyring if available
    if HAS_KEYRING and keyring:
        try:
            if value := keyring.get_password(APP_NAME, key):
                return value
        except KeyringError:
            pass

    # Finally try config env file
    return load_from_env_file().get(key)


def store_credential(
    key: str, value: str, storage_type: StorageType | None = None,
) -> None:
    """Store a credential using the specified or available storage method.

    Args:
        key: The key to store
        value: The value to store
        storage_type: Where to store the credential (if None, will use available method)

    Raises:
        typer.Exit: If keyring storage is requested but unavailable in the environment.
    """
    # If storage type is explicitly specified, use that
    if storage_type:
        if storage_type == "keyring" and not HAS_KEYRING:
            rich.print("[red]Error:[/red] Keyring storage requested but not available")
            raise typer.Exit(1)

        if storage_type == "keyring":
            if not keyring:
                rich.print(
                    "[red]Error:[/red] Keyring support is unavailable in this "
                    "environment.",
                )
                raise typer.Exit(1)
            keyring.set_password(APP_NAME, key, value)
        else:
            save_to_env_file({key: value})
        return

    # Otherwise try available methods in order
    if HAS_KEYRING and keyring:
        try:
            keyring.set_password(APP_NAME, key, value)
        except KeyringError as exc:
            rich.print(f"[yellow]Warning:[/yellow] Could not store in keyring: {exc}")
        else:
            return

    # Fall back to env file
    save_to_env_file({key: value})


def delete_credential(key: str) -> None:
    """Delete a credential from all storage locations.

    Args:
        key: The key to delete
    """
    if HAS_KEYRING and keyring:
        with suppress(KeyringError):
            keyring.delete_password(APP_NAME, key)

    # Remove from env file
    if CREDENTIALS_FILE.exists():
        try:
            credentials = load_from_env_file()
            if key in credentials:
                del credentials[key]
                save_to_env_file(credentials, merge=False)
        except OSError:
            pass


def interactive_setup() -> None:
    """Run interactive setup to configure credentials.

    Raises:
        typer.Exit: If no credential storage method is available or persistence fails.
    """
    rich.print("\n[bold]Welcome to Sonos Last.fm Scrobbler Setup![/bold]\n")

    # Explain storage options
    rich.print("[bold]Available credential storage options:[/bold]")
    options = []

    if HAS_KEYRING:
        options.append(("keyring", "System keyring (most secure)"))
    options.append(("env_file", f"Config file ({CREDENTIALS_FILE})"))

    for index, (_storage_key, desc) in enumerate(options, 1):
        rich.print(f"{index}. {desc}")

    # Get storage preference
    if options:
        choice = Prompt.ask(
            "\nWhere would you like to store your credentials?",
            choices=[str(i) for i in range(1, len(options) + 1)],
            default="1",
        )
        storage_type = options[int(choice) - 1][0]
    else:
        rich.print("[red]Error:[/red] No storage methods available!")
        raise typer.Exit(1)

    rich.print("\nPlease enter your Last.fm credentials:")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    api_key = Prompt.ask("API Key")
    api_secret = Prompt.ask("API Secret", password=True)

    # Store credentials using chosen method
    try:
        for key, value in [
            ("username", username),
            ("password", password),
            ("api_key", api_key),
            ("api_secret", api_secret),
        ]:
            store_credential(key, value, storage_type)

        rich.print(f"\n[green]✓[/green] Credentials stored using {storage_type}!")
    except (KeyringError, OSError) as exc:
        rich.print(f"\n[red]Error:[/red] Failed to store credentials: {exc}")
        raise typer.Exit(1) from exc

    # Show account info after setup
    rich.print("\nTesting connection and showing account information:")
    show_account_info()


@app.command(name="info")
def show_account_info() -> None:
    """Show Last.fm account information and your recent scrobbles.

    Raises:
        typer.Exit: If the Last.fm network cannot be initialized or API calls fail.
    """
    console = Console()

    with console.status("Connecting to Last.fm...") as status:
        network = get_lastfm_network()
        if not network:
            raise typer.Exit(1)

        try:
            # Get user info
            status.update("Getting user information...")
            user = network.get_authenticated_user()

            # Get recent tracks
            status.update("Fetching recent tracks...")
            recent_tracks = user.get_recent_tracks(limit=10)  # Get last 10 tracks

            # Get user stats
            status.update("Fetching user statistics...")
            playcount = user.get_playcount()
            reg_timestamp = user.get_registered()
            registered = datetime.fromtimestamp(int(reg_timestamp), tz=timezone.utc)

            # Create user info table
            user_table = Table(title="Last.fm User Information")
            user_table.add_column("Property", style="cyan")
            user_table.add_column("Value", style="green")

            user_table.add_row("Username", user.get_name())
            user_table.add_row("Total Scrobbles", str(playcount))
            user_table.add_row(
                "Registered Since", registered.strftime("%Y-%m-%d %H:%M:%S UTC"),
            )

            # Create recent tracks table
            if recent_tracks:
                tracks_table = Table(
                    title=f"Last {len(recent_tracks)} Scrobbled Tracks",
                )
                tracks_table.add_column("#", style="dim")
                tracks_table.add_column("Artist", style="cyan")
                tracks_table.add_column("Title", style="green")
                tracks_table.add_column("Album", style="blue")
                tracks_table.add_column("Scrobbled At", style="magenta")

                for idx, track in enumerate(recent_tracks, 1):
                    scrobbled_at = datetime.fromtimestamp(
                        int(track.timestamp), tz=timezone.utc,
                    )

                    tracks_table.add_row(
                        str(idx),
                        track.track.artist.name,
                        track.track.title,
                        track.album or "—",  # Show dash if no album
                        scrobbled_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    )

            # Print results
            console.print("\n[green]✓[/green] Successfully connected to Last.fm API!\n")
            console.print(user_table)
            if recent_tracks:
                console.print("\n", tracks_table)

        except pylast.PylastError as exc:
            console.print(f"\n[red]Error:[/red] Last.fm API error: {exc}")
            raise typer.Exit(1) from exc
        except (OSError, RuntimeError, ValueError) as exc:
            console.print(f"\n[red]Error:[/red] Unexpected error: {exc}")
            console.print("[dim]Debug: Full error details:[/dim]")
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            raise typer.Exit(1) from exc


@app.command(name="show")
def show_credentials() -> None:
    """Show stored Last.fm credentials (passwords/secrets masked) and account info."""
    console = Console()
    table = Table(title="Stored Credentials")

    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    sensitive_keys = {"password", "api_secret"}
    for key in CREDENTIAL_KEYS:
        value = get_stored_credential(key)
        if value:
            display_value = "********" if key in sensitive_keys else value
            table.add_row(key, display_value)
        else:
            table.add_row(key, "[red]not set[/red]")

    console.print(table)

    # If we have all credentials, show account info
    if all(get_stored_credential(key) for key in CREDENTIAL_KEYS):
        rich.print("\nShowing account information:")
        show_account_info()


@app.command(name="reset")
def reset_credentials() -> None:
    """Remove all stored Last.fm credentials from the system keyring."""
    if not Confirm.ask("\nAre you sure you want to remove all stored credentials?"):
        rich.print("Operation cancelled.")
        return

    for key in CREDENTIAL_KEYS:
        delete_credential(key)

    rich.print("\n[green]✓[/green] All credentials removed successfully!")


@app.command(name="setup")
def setup_credentials() -> None:
    """Configure Last.fm credentials (removes existing if any)."""
    # Check if we have any existing credentials
    has_credentials = any(get_stored_credential(key) for key in CREDENTIAL_KEYS)

    if has_credentials:
        if not Confirm.ask(
            "\nExisting credentials found. Do you want to reconfigure them?",
        ):
            rich.print("Operation cancelled.")
            return

        # Remove existing credentials
        for key in CREDENTIAL_KEYS:
            delete_credential(key)

        rich.print("[green]✓[/green] Existing credentials removed.")

    # Run setup
    interactive_setup()


@app.command()
def run(  # noqa: PLR0913, PLR0917
    setup: Annotated[
        bool,
        typer.Option(
            "--setup",
            help="Run interactive setup before starting",
            is_flag=True,
        ),
    ] = False,
    username: str | None = typer.Option(
        None,
        "--username",
        "-u",
        help="Last.fm username",
        envvar="LASTFM_USERNAME",
    ),
    password: str | None = typer.Option(
        None,
        "--password",
        "-p",
        help="Last.fm password",
        envvar="LASTFM_PASSWORD",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Last.fm API key",
        envvar="LASTFM_API_KEY",
    ),
    api_secret: str | None = typer.Option(
        None,
        "--api-secret",
        "-s",
        help="Last.fm API secret",
        envvar="LASTFM_API_SECRET",
    ),
    scrobble_interval: int = typer.Option(
        1,
        "--interval",
        "-i",
        help="Scrobbling check interval in seconds",
        envvar="SCROBBLE_INTERVAL",
    ),
    rediscovery_interval: int = typer.Option(
        10,
        "--rediscovery",
        "-r",
        help="Speaker rediscovery interval in seconds",
        envvar="SPEAKER_REDISCOVERY_INTERVAL",
    ),
    threshold: float = typer.Option(
        25.0,
        "--threshold",
        "-t",
        help="Scrobble threshold percentage",
        envvar="SCROBBLE_THRESHOLD_PERCENT",
        min=0,
        max=100,
    ),
) -> None:
    """Start the Sonos scrobbler (requires credentials).

    Monitors your Sonos speakers and scrobbles tracks to Last.fm. Can use stored
    credentials or accept them via command line options or environment variables.

    Raises:
        typer.Exit: If required credentials are missing after prompting.
    """
    if setup:
        interactive_setup()
        return

    # Get credentials from various sources
    final_username = username or get_stored_credential("username")
    final_password = password or get_stored_credential("password")
    final_api_key = api_key or get_stored_credential("api_key")
    final_api_secret = api_secret or get_stored_credential("api_secret")

    # Check if we have all required credentials
    missing = []
    if not final_username:
        missing.append("username")
    if not final_password:
        missing.append("password")
    if not final_api_key:
        missing.append("API key")
    if not final_api_secret:
        missing.append("API secret")

    if missing:
        rich.print(
            f"\n[red]Error:[/red] Missing required credentials: {', '.join(missing)}",
        )
        if Confirm.ask("\nWould you like to run the setup now?"):
            interactive_setup()
            return
        raise typer.Exit(1)

    # Set environment variables for the scrobbler
    os.environ["LASTFM_USERNAME"] = final_username
    os.environ["LASTFM_PASSWORD"] = final_password
    os.environ["LASTFM_API_KEY"] = final_api_key
    os.environ["LASTFM_API_SECRET"] = final_api_secret
    os.environ["SCROBBLE_INTERVAL"] = str(scrobble_interval)
    os.environ["SPEAKER_REDISCOVERY_INTERVAL"] = str(rediscovery_interval)
    os.environ["SCROBBLE_THRESHOLD_PERCENT"] = str(threshold)

    # Run the scrobbler
    scrobbler = SonosScrobbler()
    scrobbler.run()


def get_lastfm_network() -> pylast.LastFMNetwork | None:
    """Initialize Last.fm network with stored credentials.

    Returns:
        Initialized Last.fm network or None if credentials are missing
    """
    username = get_stored_credential("username")
    password = get_stored_credential("password")
    api_key = get_stored_credential("api_key")
    api_secret = get_stored_credential("api_secret")

    if not all([username, password, api_key, api_secret]):
        rich.print(
            "[red]Error:[/red] Missing credentials. Please run 'sonos-lastfm setup' "
            "to configure.",
        )
        return None

    try:
        return pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret,
            username=username,
            password_hash=pylast.md5(password),
        )
    except pylast.PylastError as exc:
        rich.print(f"[red]Error:[/red] Failed to initialize Last.fm network: {exc}")
        return None


@app.command(name="recent")
def show_recent_tracks(
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of recent tracks to show",
        min=1,
        max=50,
    ),
) -> None:
    """Show recently scrobbled tracks.

    Raises:
        typer.Exit: If the Last.fm network is unavailable or API calls fail.
    """
    console = Console()

    with console.status("Connecting to Last.fm...") as status:
        network = get_lastfm_network()
        if not network:
            raise typer.Exit(1)

        try:
            status.update("Getting authenticated user...")
            user = network.get_authenticated_user()

            status.update(f"Fetching last {limit} tracks...")
            recent_tracks = user.get_recent_tracks(limit=limit)

            if not recent_tracks:
                console.print("[yellow]No recent tracks found.[/yellow]")
                return

            # Create tracks table
            tracks_table = Table(title=f"Last {len(recent_tracks)} Scrobbled Tracks")
            tracks_table.add_column("#", style="dim")
            tracks_table.add_column("Artist", style="cyan")
            tracks_table.add_column("Title", style="green")
            tracks_table.add_column("Album", style="blue")
            tracks_table.add_column("Scrobbled At", style="magenta")

            status.update("Processing track information...")
            for idx, track in enumerate(recent_tracks, 1):
                scrobbled_at = datetime.fromtimestamp(
                    int(track.timestamp), tz=timezone.utc,
                )

                tracks_table.add_row(
                    str(idx),
                    track.track.artist.name,
                    track.track.title,
                    track.album or "—",  # Show dash if no album
                    scrobbled_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                )

            console.print(tracks_table)

        except pylast.PylastError as exc:
            console.print(f"\n[red]Error:[/red] Last.fm API error: {exc}")
            raise typer.Exit(1) from exc
        except (OSError, RuntimeError, ValueError) as exc:
            console.print(f"\n[red]Error:[/red] Unexpected error: {exc}")
            console.print("[dim]Debug: Full error details:[/dim]")
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            raise typer.Exit(1) from exc


def main() -> None:
    """Entry point for the CLI."""
    app()
