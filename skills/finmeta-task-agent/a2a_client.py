#!/usr/bin/env python3
"""
FinMeta Task Agent A2A Client.

Usage:
  python a2a_client.py --list                          # List task agents
  python a2a_client.py --agent 1 --args '{"input":"600519.SH"}'  # Call agent
  python a2a_client.py --agent 1 --args '{"input":"600519.SH"}' --wait  # Call + poll

Token: reads FINMETA_ACCESS_TOKEN env var first, then ~/.finmeta/access_token.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_BASE = os.environ.get("FINTOOLS_API_BASE", "https://fin-meta.net")
API_PREFIX = "/api/v1"


def load_token():
    token = os.environ.get("FINMETA_ACCESS_TOKEN")
    if token:
        return token
    token_file = os.path.expanduser("~/.finmeta/access_token")
    try:
        with open(token_file) as f:
            token = f.read().strip()
            if token:
                return token
    except FileNotFoundError:
        pass
    return None


def api_request(method, path, body=None):
    token = load_token()
    if not token:
        sys.exit("ERROR: FINMETA_ACCESS_TOKEN not set and ~/.finmeta/access_token not found.\n"
                 "Run finmeta-plugin setup first: https://fin-meta.net/profile → Access Token tab.")
    url = f"{API_BASE}{API_PREFIX}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        sys.exit(f"HTTP {e.code}: {body_text}")


def list_task_agents():
    """Fetch public agents and filter to task agents (type=agent, called via A2A)."""
    data = api_request("GET", "/public/agents?limit=100")
    items = data.get("items", data.get("agents", []))
    task_agents = [a for a in items if a.get("asset_type") == "agent"]
    api_agents = [a for a in items if a.get("asset_type") == "api"]

    print(f"Total: {len(items)} agents (Task: {len(task_agents)}, API: {len(api_agents)})\n")

    if task_agents:
        print("=== Task Agents (A2A) ===")
        for a in task_agents:
            labels = a.get("labels_system", [])
            health = "⚠" if "health:unhealthy" in labels else "✓"
            print(f"  [{a['id']}] {a['name']}  {health}"
                  f"  category={a.get('agent_category','?')}"
                  f"  market={a.get('asset_market','?')}"
                  f"  owner={a.get('owner','?')}")
            if a.get("description"):
                desc = a["description"].split("\n")[0][:120]
                print(f"      {desc}")
        print()

    if api_agents:
        print("=== API Agents (HTTP) — use invoke-api-agent ===")
        for a in api_agents:
            print(f"  [{a['id']}] {a['name']}  category={a.get('agent_category','?')}  owner={a.get('owner','?')}")
        print()

    return task_agents


def build_a2a_body(agent_args):
    """Build the A2A JSON-RPC message body with agent_args in the correct nested path.

    Backend extracts: params.message.parts[0].metadata.agent_args
    """
    return {
        "params": {
            "message": {
                "parts": [{
                    "metadata": {
                        "agent_args": agent_args
                    }
                }]
            }
        }
    }


def call_agent(agent_id, agent_args):
    """POST to the agent's A2A endpoint. Returns the response dict."""
    body = build_a2a_body(agent_args)
    return api_request("POST", f"/agents/{agent_id}/a2a/", body)


def poll_run(agent_id, run_id, timeout=300, interval=5):
    """Poll for run completion. Returns the final run record."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = api_request("GET", f"/agents/{agent_id}/runs?limit=5")
        runs = data.get("runs", [])
        for r in runs:
            if r.get("run_id") == run_id:
                status = r.get("status")
                if status == "completed":
                    return r
                elif status in ("failed", "error", "cancelled"):
                    return r
        print(f"  … {run_id[:8]}… still running ({int(deadline - time.time())}s left)", file=sys.stderr)
        time.sleep(interval)
    sys.exit(f"Timeout: run {run_id} did not complete within {timeout}s")


def main():
    parser = argparse.ArgumentParser(description="FinMeta Task Agent A2A Client")
    parser.add_argument("--list", action="store_true", help="List available task agents")
    parser.add_argument("--agent", type=str, metavar="ID", help="Agent ID to call")
    parser.add_argument("--args", type=str, metavar="JSON", default="{}",
                        help='Agent arguments as JSON, e.g. \'{"input":"600519.SH"}\'')
    parser.add_argument("--wait", action="store_true",
                        help="Poll for result after job-mode call (blocks until completed)")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Poll timeout in seconds (default: 300)")
    opts = parser.parse_args()

    if opts.list:
        list_task_agents()
        return

    if not opts.agent:
        parser.print_help()
        sys.exit(1)

    try:
        agent_args = json.loads(opts.args)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: invalid JSON for --args: {e}")

    print(f"Calling agent {opts.agent} with args: {json.dumps(agent_args)}")
    resp = call_agent(opts.agent, agent_args)
    print(json.dumps(resp, indent=2, ensure_ascii=False))

    if opts.wait and resp.get("run_id"):
        run_id = resp["run_id"]
        print(f"\nPolling run {run_id}…", file=sys.stderr)
        run = poll_run(opts.agent, run_id, timeout=opts.timeout)
        status = run.get("status")
        result = run.get("result")
        print(f"\nStatus: {status}")
        print(f"Result: {result}")
        print(json.dumps(run, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
