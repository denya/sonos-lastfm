# Sonos Last.fm Scrobbler

[![PyPI](https://img.shields.io/pypi/v/sonos-lastfm)](https://pypi.org/project/sonos-lastfm/)
[![Python](https://img.shields.io/pypi/pyversions/sonos-lastfm)](https://pypi.org/project/sonos-lastfm/)

![sonos lastfm](https://github.com/user-attachments/assets/6c84174d-a927-4801-8800-e2343d1646d7)

Automatically scrobble what's playing on your Sonos speakers to your Last.fm profile.

## The problem

If you use Last.fm, you know the value of a complete listening history. Some of us have been scrobbling for 10, 15, even 20 years — and that data tells a story.

But Sonos doesn't support Last.fm. There's no native integration, no plugin, no setting to flip. Every song you play on your Sonos speakers is a gap in your scrobbling history.

## The solution

**sonos-lastfm** is a lightweight CLI tool that monitors your local network for Sonos playback and scrobbles every track to Last.fm automatically.

Run it on any always-on device in your home — a Raspberry Pi, a Mac Mini, an old laptop, or any Linux server — and never miss a scrobble again. It works as a background daemon, so once you set it up, you can forget about it.

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

## AI-powered setup

Want an AI agent to handle the full setup for you — installing, configuring credentials, and setting up a persistent daemon? Use the included setup skill with any agent that supports [open agent skills](https://github.com/vercel-labs/skills) (Claude Code, Cursor, Windsurf, Codex, etc.).

**Option A** — Install the skill directly (no clone needed):

```bash
npx skills add denya/sonos-lastfm@setup-sonos-lastfm
```

Then ask your agent to "set up sonos-lastfm as a daemon."

**Option B** — Clone the repo and use the skill from source:

```bash
git clone https://github.com/denya/sonos-lastfm.git
cd sonos-lastfm
npx skills add ./skills/setup-sonos-lastfm
```

The skill covers Linux (systemd), macOS (launchd), and Windows (Task Scheduler), guides you through getting Last.fm API keys, and ensures you're always running the latest version from PyPI.

## Scrobble rules

- Track is scrobbled after **25%** played (configurable via `--threshold`) or **4 minutes**, whichever comes first
- Same track won't be scrobbled again within 30 minutes

## License

MIT
