# Sonos Last.fm Scrobbler

![sonos lastfm](https://github.com/user-attachments/assets/6c84174d-a927-4801-8800-e2343d1646d7)

Automatically scrobble what's playing on your Sonos speakers to your Last.fm profile.

## Get started in 2 minutes

### 1. Install

```bash
pip install sonos-lastfm
```

Requires Python 3.10+ and Sonos speakers on the same network.

### 2. Get a free Last.fm API key

You need an API key so the app can talk to Last.fm on your behalf. It's free and takes 30 seconds:

1. Open https://www.last.fm/api/account/create
2. Fill in the form — app name can be anything (e.g. "my sonos scrobbler"), other fields don't matter
3. Submit — you'll see your **API key** and **Shared secret**. Keep this page open, you'll need both in the next step

### 3. Run setup

```bash
sonos-lastfm setup
```

The setup wizard will ask for four things:

| Credential | What it is |
|---|---|
| **Username** | Your Last.fm username (the one you log in with) |
| **Password** | Your Last.fm account password |
| **API key** | From step 2 above |
| **API secret** | The "Shared secret" from step 2 above |

The wizard validates your credentials immediately, so you'll know right away if something's wrong.

### 4. Start scrobbling

```bash
sonos-lastfm run
```

That's it! Play something on your Sonos and it will show up on your Last.fm profile.

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
