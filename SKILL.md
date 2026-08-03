---
name: finmeta-plugin
description: Set up FinMeta API credentials (FINMETA_ACCESS_TOKEN + simulation account_id) in ~/.finmeta/config.json. Use when any FinMeta skill needs credentials, the user asks about authentication, or a 401 error occurs. Single source of truth — all other finmeta-plugin skills depend on it.
---

# FinMeta Plugin — Credentials Setup

Single source of truth for FinMeta credentials. Every skill in this plugin reads from **`~/.finmeta/config.json`** at runtime — no `export`, no agent memory.

## How credential storage works

All credentials persist to **`~/.finmeta/config.json`** (`chmod 600`):

```json
{
  "access_token": "<user PAT>",
  "accounts": { "ashare": 26, "usstock": null, "crypto": null }
}
```

- `access_token` — user PAT, sent as `Authorization: Bearer` for all FinMeta API calls
- `accounts.<market>` — simulation account_id per market (A-Share needs it; US Stock / Crypto auto-resolve)

Skills read this file directly at runtime: simulation `api.py` reads via Python; `invoke-api-agent` extracts via `python3 -c json`. **Never store credentials in agent memory** — always this file, always re-read it.

If the file or `access_token` field is missing, the skill stops and asks the user to run this setup first.

## Setup (first time or after token expiry)

### Step 1: Get your token

1. Open **https://fin-meta.net/profile** (cloud) or `http://localhost/profile` (local dev)
2. Click **"Access Token"** tab
3. Copy the token

### Step 2: Save the token to config.json

```bash
mkdir -p ~/.finmeta
python3 -c "import json,os; p=os.path.expanduser('~/.finmeta/config.json'); cfg=json.load(open(p)) if os.path.exists(p) else {}; cfg['access_token']='<paste-token-here>'; json.dump(cfg,open(p,'w'),indent=2)"
chmod 600 ~/.finmeta/config.json
```

### Step 3: Verify

```bash
TOKEN=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.finmeta/config.json'))).get('access_token',''))")
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/symbols?limit=1"
# Should return 200
```

If you get **401**, the token is expired — get a new one from Profile and repeat Step 2.

## For simulation trading: A-Share account ID

Only `finmeta-simulation-skill` A-Share market needs an account_id (US Stock / Crypto auto-resolve). Save it to the same config.json:

```bash
python ashare/api.py --account-id 26   # writes accounts.ashare in ~/.finmeta/config.json
```

Find your account ID: My Simulation page → click the ID chip to copy.

## Token naming convention

| Name | Use |
|------|-----|
| `FINMETA_ACCESS_TOKEN` | **User PAT** — all FinMeta API calls (Bearer auth) |
| `GITEA_ACCESS_TOKEN` | **Admin/service token** — backend only, never expose to skills |

The old names `FINTOOLS_ACCESS_TOKEN` / `FINTOOLS_API_TOKEN` are deprecated — always use `FINMETA_ACCESS_TOKEN`.
