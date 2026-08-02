---
name: finmeta-plugin
description: Set up FinMeta API credentials (FINMETA_ACCESS_TOKEN). Use when any FinMeta skill needs a token, the user asks about authentication, or a 401 error occurs. This is the single source of truth for FinMeta token management — all other finmeta-plugin skills depend on it.
---

# FinMeta Plugin — Token Setup

Single source of truth for `FINMETA_ACCESS_TOKEN`. Every skill in this plugin uses the same token.

## How token storage works

The token is persisted to **`~/.finmeta/access_token`** (a single-line file, `chmod 600`). All plugin skills source it the same way:

```bash
export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token 2>/dev/null)
```

If the file doesn't exist or is empty, the skill stops and asks the user to run this setup first.

## Setup (first time or after token expiry)

### Step 1: Get your token

1. Open **https://fin-meta.net/profile**
2. Click **"Access Token"** tab
3. Copy the token

### Step 2: Save the token (persistent)

```bash
mkdir -p ~/.finmeta
echo "<paste-token-here>" > ~/.finmeta/access_token
chmod 600 ~/.finmeta/access_token
```

Then load it into the current session:

```bash
export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token)
```

### Step 3: Verify

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/symbols?limit=1"
# Should return 200
```

If you get **401**, the token is expired — get a new one from Profile and repeat Step 2.

### Step 4 (optional): Auto-load on shell start

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token 2>/dev/null)
```

## For simulation trading: A-Share account ID

Only needed for `finmeta-simulation-skill` (A-Share market):

```bash
export FINTOOLS_SIMULATION_ACCOUNT_ID=123
```

Find your account ID: My Simulation page → click the ID chip to copy.

## Token naming convention

| Name | Use |
|------|-----|
| `FINMETA_ACCESS_TOKEN` | **User PAT** — all FinMeta API calls (Bearer auth) |
| `GITEA_ACCESS_TOKEN` | **Admin/service token** — backend only, never expose to skills |

The old names `FINTOOLS_ACCESS_TOKEN` / `FINTOOLS_API_TOKEN` are deprecated — always use `FINMETA_ACCESS_TOKEN`.
