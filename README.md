# Personal Home Assistant Dashboard

A tiny self-hosted dashboard that runs your Python device-control scripts (SwitchBot, lights, etc.) with a tap — from a browser, as an installed PWA on iPhone, or via iOS Shortcuts from your Apple Watch.

Stack: FastAPI + vanilla HTML/JS + nginx + systemd. Runs on a Raspberry Pi.

## How it works

```
Apple Watch / iPhone / Browser ──► nginx (TLS) ──► FastAPI ──► python3 scripts/switchbot_press.py
```

Each button in the UI corresponds to one entry in `backend/actions.toml`, which maps an `id` to a script file under `backend/scripts/`. The API whitelists those IDs and never executes a raw path.

## Add a new action

1. Drop your script at `backend/scripts/<name>.py`. It must exit 0 on success.
2. Add to `backend/actions.toml`:
   ```toml
   [[action]]
   id = "lights_off"
   label = "All Lights Off"
   script = "lights_off.py"
   icon = "bulb"
   timeout_s = 10
   ```
3. `sudo systemctl restart dashboard` on the Pi.

Supported icon keys: `toggle`, `bulb`, `lock`, `fan`, `bolt`, `plug`, `tv`, `speaker`.

## Local dev (Windows/macOS/Linux)

```bash
cd backend
python -m venv ../.venv
../.venv/bin/pip install -r requirements.txt   # Windows: ..\.venv\Scripts\pip
cp .env.example .env                            # then edit DASHBOARD_TOKEN
cd ..
.venv/bin/uvicorn backend.main:app --reload
```

Open <http://localhost:8000>. The first visit prompts for the token (settings gear).

## Raspberry Pi deploy

```bash
git clone <this repo> ~/Personal-Home-Assistant-Dashboard
cd ~/Personal-Home-Assistant-Dashboard
bash deploy/install.sh
```

The installer:

- creates a venv and installs requirements,
- generates a random `DASHBOARD_TOKEN` into `backend/.env` (printed to stdout — save it),
- creates a self-signed TLS cert for `dashboard.local`,
- installs and starts the `dashboard` systemd service,
- installs the nginx site.

Verify:

```bash
sudo systemctl status dashboard
curl -k -H "Authorization: Bearer $TOKEN" https://dashboard.local/api/actions
```

## Install as a PWA on iPhone

1. Open `https://dashboard.local` in Safari. Accept the self-signed cert once.
2. Tap the settings gear → paste the token → Save.
3. Share → **Add to Home Screen**.

The dashboard now launches in standalone mode with its own icon.

## Apple Watch via Shortcuts

The Watch cannot browse PWAs directly, so each action gets its own Shortcut:

1. Open **Shortcuts** on iPhone → **+**.
2. Add action **Get Contents of URL**:
   - URL: `https://dashboard.local/api/run/switchbot_press`
   - Method: `POST`
   - Headers: `Authorization: Bearer <your-token>`
3. Name it ("Press SwitchBot"), enable **Show on Apple Watch**.
4. On the Watch, either use the Shortcuts complication or say "Hey Siri, press SwitchBot".

Repeat per action. If you have many, create one Shortcut that uses **Choose from Menu** and fans out to separate URLs.

## Security

- Bearer token auth (`DASHBOARD_TOKEN` in `backend/.env`), validated in constant time.
- Uvicorn binds to `127.0.0.1`; only nginx is exposed.
- Scripts are whitelisted; paths escaping `backend/scripts/` are rejected at startup.
- `subprocess` is invoked with a fixed argv (no `shell=True`).
- Do **not** port-forward the Pi. For remote access, put it behind Tailscale — Shortcuts work unchanged.

## File layout

```
backend/
  main.py           # FastAPI app
  registry.py       # load + validate actions.toml
  runner.py         # async subprocess wrapper with timeout + logging
  settings.py       # env + paths
  actions.toml      # registry
  scripts/          # your Python scripts
frontend/           # static PWA (no build step)
deploy/             # systemd unit, nginx conf, install.sh
```

Run logs land in `~/.dashboard/run.log` as one JSON object per invocation.
