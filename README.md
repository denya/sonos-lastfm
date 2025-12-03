# Sonos to Last.fm Scrobbler

![sonos lastfm](https://github.com/user-attachments/assets/6c84174d-a927-4801-8800-e2343d1646d7)

This script automatically scrobbles music playing on your Sonos speakers to Last.fm.

## Features

- Automatic Sonos speaker discovery on your network
- Real-time track monitoring and scrobbling
- Smart duplicate scrobble prevention
- Multi-speaker support
- Local data persistence for tracking scrobble history
- Secure credential storage using system keyring (when available)
- Modern CLI interface with interactive setup

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Basic installation
pip install sonos-lastfm

# Optional: Install keyring backend for secure credential storage
pip install keyring keyrings.alt
```

### Option 2: Local Development Setup

1. Install `uv` (Python package installer):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Setup and run using Make commands:
   ```bash
   # Setup Python environment with uv
   make setup

   # Install dependencies
   make install

   # For development, install additional tools (optional)
   make install-dev

   # Optional: Install keyring backend for secure credential storage
   pip install keyring keyrings.alt
   ```

   Run `make help` to see all available commands.

## Usage

### Quick Start

1. Run the interactive setup:
   ```bash
   sonos-lastfm setup
   ```
   If you have a keyring backend installed, credentials will be stored securely.
   Otherwise, you'll be prompted to store them in your environment or .env file.

2. Start scrobbling:
   ```bash
   sonos-lastfm
   ```

### Command Line Options

```bash
sonos-lastfm [OPTIONS] COMMAND [ARGS]...

Commands:
  run      Run the Sonos Last.fm scrobbler (default if no command specified)
  show     Show stored credentials (passwords/secrets masked)
  reset    Remove all stored credentials
  resetup  Remove existing credentials and run setup again
  test     Test Last.fm API connectivity and show user information

Options:
  -u, --username TEXT            Last.fm username
  -p, --password TEXT           Last.fm password
  -k, --api-key TEXT           Last.fm API key
  -s, --api-secret TEXT        Last.fm API secret
  -i, --interval INTEGER       Scrobbling check interval in seconds [default: 1]
  -r, --rediscovery INTEGER    Speaker rediscovery interval in seconds [default: 10]
  -t, --threshold FLOAT        Scrobble threshold percentage [default: 25.0]
  --setup                      Run interactive setup
  --help                       Show this message and exit
```

### Credential Management

The CLI provides several commands to manage your Last.fm credentials:

1. Show stored credentials:
   ```bash
   sonos-lastfm show
   ```
   This will display your stored credentials with sensitive values masked.

2. Reset (remove) all credentials:
   ```bash
   sonos-lastfm reset
   ```
   This will remove all stored credentials from your system keyring.

3. Reconfigure credentials:
   ```bash
   sonos-lastfm resetup
   ```
   This will remove existing credentials and run the interactive setup again.

### Testing Last.fm Connection

Before starting the scrobbler, you can test your Last.fm API connection:

```bash
sonos-lastfm test
```

This will:
1. Test the connection to Last.fm API
2. Show your user information (username, total scrobbles, registration date)
3. Display your most recent scrobbled track

Use this command to verify your credentials are working correctly before starting the scrobbler.

### Configuration Methods

You can configure the scrobbler in several ways (in order of precedence):

1. Command line arguments:
   ```bash
   sonos-lastfm --username "your_username" --api-key "your_api_key"
   ```

2. Environment variables:
   ```bash
   export LASTFM_USERNAME=your_username
   export LASTFM_PASSWORD=your_password
   export LASTFM_API_KEY=your_api_key
   export LASTFM_API_SECRET=your_api_secret
   export SCROBBLE_INTERVAL=1
   export SPEAKER_REDISCOVERY_INTERVAL=10
   export SCROBBLE_THRESHOLD_PERCENT=25
   
   sonos-lastfm
   ```

3. Secure keyring storage (recommended if available):
   ```bash
   # Store credentials securely (requires keyring backend)
   sonos-lastfm --setup
   
   # Run with stored credentials
   sonos-lastfm
   ```

4. Environment file (.env):
   Create a `.env` file in your working directory:
   ```bash
   LASTFM_USERNAME=your_username
   LASTFM_PASSWORD=your_password
   LASTFM_API_KEY=your_api_key
   LASTFM_API_SECRET=your_api_secret
   ```

### Docker Setup (Linux Only)

> Note: Docker setup is not recommended on macOS due to network mode limitations affecting Sonos discovery.

1. Create a `.env` file with your Last.fm credentials:
   ```bash
   LASTFM_USERNAME=your_username
   LASTFM_PASSWORD=your_password
   LASTFM_API_KEY=your_api_key
   LASTFM_API_SECRET=your_api_secret
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Scrobbling Rules

The script follows configurable scrobbling rules:
- A track is scrobbled when either:
  - Configured percentage of the track has been played (default: 25%, range: 0-100), OR
  - 4 minutes (240 seconds) of the track have been played
- For repeated plays of the same track:
  - Enforces a 30-minute minimum interval between scrobbles of the same track
  - Prevents duplicate scrobbles during continuous play

## Data Storage

- Credentials are stored securely in your system's keyring
- Scrobble history and currently playing information is stored in:
  - `~/.config/sonos-lastfm/last_scrobbled.json`
  - `~/.config/sonos-lastfm/currently_playing.json`

## Requirements

- Python 3.11+
- Sonos speakers on your network
- Last.fm account and API credentials
  - Get your API credentials at: https://www.last.fm/api/account/create
- Optional but recommended:
  - Keyring backend for secure credential storage:
    ```bash
    pip install keyring keyrings.alt
    ```
  - Without a keyring backend, credentials must be stored in environment variables or .env file

## Troubleshooting

Common issues and solutions:
- No speakers found: Ensure your computer is on the same network as your Sonos system
- Scrobbling not working: Check your Last.fm credentials with `sonos-lastfm --setup`
- Missing scrobbles: Verify that both artist and title information are available for the track
- Keyring errors: If you see keyring-related errors, either:
  1. Install a keyring backend: `pip install keyring keyrings.alt`
  2. Use environment variables or .env file for credentials instead
