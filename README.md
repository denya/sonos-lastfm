# Sonos Last.fm Scrobbler

![sonos lastfm](https://github.com/user-attachments/assets/6c84174d-a927-4801-8800-e2343d1646d7)

Scrobbles music from your Sonos speakers to Last.fm.

## Install

```bash
pip install sonos-lastfm
```

Requires Python 3.14+ and Sonos speakers on the same network.

## Get Last.fm API credentials

1. Go to https://www.last.fm/api/account/create
2. Fill in the form (app name can be anything, e.g. "sonos-scrobbler")
3. You'll get an **API key** and **API secret**
4. You also need your Last.fm **username** and **password**

## Setup credentials

Interactive setup (stores in `~/.sonos_lastfm/.env` or system keyring):

```bash
sonos-lastfm setup
```

Or pass via environment / `.env` file:

```
LASTFM_USERNAME=your_username
LASTFM_PASSWORD=your_password
LASTFM_API_KEY=your_api_key
LASTFM_API_SECRET=your_api_secret
```

## CLI usage

```bash
sonos-lastfm run                # start scrobbling (interactive, with progress bar)
sonos-lastfm run --daemon       # start scrobbling (no progress display, for services)
sonos-lastfm run --interval 5   # check every 5s instead of 1s
sonos-lastfm info               # show account info and recent scrobbles
sonos-lastfm recent             # show last 10 scrobbled tracks
sonos-lastfm show               # show stored credentials (masked)
sonos-lastfm reset              # delete stored credentials
```

All `run` options: `sonos-lastfm run --help`

## Run as a systemd service

Create `~/.config/systemd/user/sonos-lastfm.service`:

```ini
[Unit]
Description=Sonos Last.fm Scrobbler
After=network-online.target

[Service]
Type=simple
ExecStart=%h/.local/bin/sonos-lastfm run --daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

Then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now sonos-lastfm
journalctl --user -u sonos-lastfm -f   # watch logs
```

In daemon mode, only song changes, scrobbles, and errors are logged.

## Scrobble rules

- Track is scrobbled after **25%** played (configurable via `--threshold`) or **4 minutes**, whichever comes first
- Same track won't be scrobbled again within 30 minutes

## License

MIT
