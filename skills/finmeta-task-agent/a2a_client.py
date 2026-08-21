#!/usr/bin/env python3
"""
FinMeta Task Agent A2A Client (minimal).

Task agents run as async K8s Jobs — a call returns immediately with a run_id,
then the agent runs for several minutes (some >10 min) before producing a
result. This client submits the call and (with --wait) polls the backend
/runs endpoint until done, then downloads + extracts report.zip and prints
the decision.

Usage:
  python a2a_client.py --list                                              # list task agents + input schemas + eval summary
  python a2a_client.py --detail 1                                          # agent detail + stability / eval test results
  python a2a_client.py --agent 1 --args '{"stock_code":"600519.SH"}'       # submit, return run_id
  python a2a_client.py --agent 1 --args '{"stock_code":"600519.SH"}' --wait # submit + poll + download report

Token: FINMETA_ACCESS_TOKEN env var → ~/.finmeta/config.json (access_token).
HTTP via curl (not urllib) — fin-meta.net sits behind Cloudflare bot-fight.

Exit codes: 0 = completed, 1 = run failed, 124 = poll timeout (agent may still be running).
"""

import argparse
import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

API_BASE = os.environ.get("FINTOOLS_API_BASE", "https://fin-meta.net")
API_PREFIX = "/api/v1"


def load_token():
    """Same precedence as the other plugin skills (simulation api.py):
    1. FINMETA_ACCESS_TOKEN env var
    2. ~/.finmeta/config.json  →  access_token   (SSOT)
    """
    token = os.environ.get("FINMETA_ACCESS_TOKEN")
    if token:
        return token
    config_path = os.path.expanduser("~/.finmeta/config.json")
    try:
        with open(config_path) as f:
            t = json.load(f).get("access_token")
            if t:
                return t
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return None


def api_request(method, path, body=None):
    token = load_token()
    if not token:
        sys.exit("ERROR: no token. Set FINMETA_ACCESS_TOKEN or run finmeta-plugin setup "
                 "(https://fin-meta.net/profile → Access Token).\n")
    url = f"{API_BASE}{API_PREFIX}{path}"
    cmd = ["curl", "-sS", "-X", method, url,
           "-H", f"Authorization: Bearer {token}",
           "-H", "Content-Type: application/json"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        sys.exit(f"curl failed: {res.stderr.strip()}")
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        sys.exit(f"non-JSON response (Cloudflare?): {res.stdout[:300]}")


def list_task_agents():
    data = api_request("GET", "/public/agents?limit=100")
    items = data.get("items", data.get("agents", []))
    task_agents = [a for a in items if a.get("asset_type") == "agent"]
    api_agents = [a for a in items if a.get("asset_type") == "api"]
    print(f"Total: {len(items)} agents (Task: {len(task_agents)}, API: {len(api_agents)})\n")

    print("=== Task Agents (A2A, async job) ===")
    for a in task_agents:
        labels = a.get("labels_system", [])
        health = "unhealthy" if "health:unhealthy" in labels else "ok"
        print(f"  [{a['id']}] {a['name']} ({health})  "
              f"category={a.get('agent_category')}  market={a.get('asset_market')}  owner={a.get('owner')}")
        schema = a.get("input_schema") or {}
        if isinstance(schema, dict) and schema:
            fields = [f'{k}: {v.get("type","?")}{"*" if v.get("required") else ""}' for k, v in schema.items()]
            print(f"      args: {{{', '.join(fields)}}}")
        if a.get("description"):
            print(f"      {a['description'].splitlines()[0][:110]}")
        # Show latest eval result if available
        tr = a.get("test_results")
        if tr and tr.get("eval_tests"):
            et = tr["eval_tests"][0]  # latest
            ttype = et.get("test_type") or "?"
            status = et.get("status") or "?"
            summary = et.get("summary") or ""
            ts = et.get("created_at") or ""
            print(f"      eval: {ttype}={status}  @ {ts}")
            if summary:
                print(f"        {summary[:130]}")
    print()

    if api_agents:
        print("=== API Agents (sync HTTP — use invoke-api-agent, not this) ===")
        for a in api_agents:
            print(f"  [{a['id']}] {a['name']}  owner={a.get('owner')}")
            tr = a.get("test_results")
            if tr and tr.get("eval_tests"):
                et = tr["eval_tests"][0]
                ttype = et.get("test_type") or "?"
                status = et.get("status") or "?"
                ts = et.get("created_at") or ""
                summary = et.get("summary") or ""
                print(f"      eval: {ttype}={status}  @ {ts}")
                if summary:
                    print(f"        {summary[:130]}")
    print()
    return task_agents


def show_agent_detail(agent_id):
    """Fetch and display agent detail with eval / stability test results."""
    data = api_request("GET", f"/public/agents/{agent_id}")
    if not data or "id" not in data:
        sys.exit(f"ERROR: agent {agent_id} not found or not listed.")
    print(f"=== Agent Detail ===")
    print(f"  id           : {data['id']}")
    print(f"  name         : {data.get('name')}")
    print(f"  author       : {data.get('author')}")
    print(f"  owner        : {data.get('owner')}")
    print(f"  type         : {data.get('asset_type')}")
    print(f"  category     : {data.get('agent_category')}")
    print(f"  market       : {data.get('asset_market')}")
    print(f"  instrument   : {data.get('asset_instrument')}")
    desc = data.get("description") or ""
    if desc:
        print(f"  description  : {desc.splitlines()[0][:120]}")
    print(f"  status       : {data.get('market_status')}")
    labels = data.get("labels_system", [])
    if labels:
        print(f"  labels       : {', '.join(labels)}")

    tr = data.get("test_results")
    if not tr:
        print("\n  (no test results)")
        return

    # Skill tests
    skill_tests = tr.get("skill_tests", [])
    if skill_tests:
        print(f"\n--- Skill Tests ({len(skill_tests)} bound skill(s)) ---")
        for st in skill_tests:
            verdict = st.get("verdict") or "?"
            name = st.get("test_repo_name") or f"skill#{st.get('test_repo_id')}"
            ts = st.get("created_at") or ""
            print(f"  {name}: {verdict.upper()}  @ {ts}")
            analysis = st.get("analysis_text") or ""
            if analysis:
                print(f"    {analysis[:150]}")

    # Eval tests (stability / performance / ...)
    eval_tests = tr.get("eval_tests", [])
    if eval_tests:
        print(f"\n--- Eval Tests ({len(eval_tests)} run(s)) ---")
        for et in eval_tests:
            ttype = et.get("test_type") or "?"
            status = et.get("status") or "?"
            summary = et.get("summary") or ""
            ts = et.get("created_at") or ""
            payload = et.get("result_payload") or {}
            # Extract key metrics from result_payload if present
            metrics = ""
            if isinstance(payload, dict):
                runs = payload.get("runs") or payload.get("total_runs") or payload.get("iterations") or ""
                avg = payload.get("avg_pass_rate") or payload.get("pass_rate") or payload.get("accuracy") or ""
                if runs:
                    metrics += f"runs={runs}"
                if avg:
                    metrics += f", avg={avg}" if metrics else f"avg={avg}"
            print(f"  {ttype}: {status}  @ {ts}")
            if metrics:
                print(f"    {metrics}")
            if summary:
                print(f"    {summary[:200]}")
            if isinstance(payload, dict) and not metrics:
                # Fallback: show top-level keys
                keys = [k for k in payload.keys() if not k.startswith("_")]
                if keys:
                    print(f"    payload keys: {', '.join(keys[:8])}")


def build_a2a_body(agent_args):
    """Wrap agent_args in the A2A JSON-RPC path the backend extracts:
    params.message.parts[0].metadata.agent_args → injected as Pod AGENT_ARGS env."""
    return {"params": {"message": {"parts": [{"metadata": {"agent_args": agent_args}}]}}}


def submit(agent_id, agent_args):
    return api_request("POST", f"/agents/{agent_id}/a2a/", build_a2a_body(agent_args))


def get_run(agent_id, run_id):
    data = api_request("GET", f"/agents/{agent_id}/runs?limit=10")
    for r in data.get("runs", []):
        if r.get("run_id") == run_id:
            return r
    return None


def wait_for_run(agent_id, run_id, timeout=900, interval=30):
    """Poll /runs until the run reaches a terminal state.
    Returns the run dict on completion/failure, or None on timeout (caller distinguishes)."""
    deadline = time.time() + timeout
    start = time.time()
    last_status = None
    while time.time() < deadline:
        r = get_run(agent_id, run_id)
        if not r:
            print(f"  [{int(time.time()-start)}s] run not found yet, retrying...", file=sys.stderr)
        else:
            status = r.get("status")
            if status != last_status:
                print(f"  [{int(time.time()-start)}s] status: {status}", file=sys.stderr)
                last_status = status
            if status in ("completed", "failed", "error", "cancelled"):
                return r
        time.sleep(interval)
    return None  # timeout — NOT a failure, agent may still be running


def default_run_dir(agent_id, run):
    """~/.finmeta/runs/agent-<id>_<YYYYMMDD-HHMMSS>/ — timestamp from the run's created_at."""
    ts = ""
    created = run.get("created_at") or ""
    if created:
        try:
            from datetime import datetime
            ts = datetime.fromisoformat(created).strftime("%Y%m%d-%H%M%S")
        except (ValueError, TypeError):
            ts = ""
    folder = f"agent-{agent_id}" + (f"_{ts}" if ts else "")
    return Path.home() / ".finmeta" / "runs" / folder


def download_and_extract(report_url, run_id, out_dir):
    """Download report.zip via curl and extract. Returns (action, extract_dir)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"report_{run_id[:8]}.zip"
    res = subprocess.run(["curl", "-sS", report_url, "-o", str(zip_path)], capture_output=True, text=True)
    if res.returncode != 0 or not zip_path.exists() or zip_path.stat().st_size < 100:
        print(f"  download failed: {res.stderr.strip() or 'empty zip'}", file=sys.stderr)
        return None, out_dir
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)
    # read decision from reports/output.json
    action = None
    output_json = out_dir / "reports" / "output.json"
    if output_json.exists():
        try:
            action = json.loads(output_json.read_text()).get("action")
        except json.JSONDecodeError:
            pass
    return action, out_dir / "reports"


def main():
    p = argparse.ArgumentParser(description="FinMeta Task Agent A2A client (minimal)")
    p.add_argument("--list", action="store_true")
    p.add_argument("--detail", metavar="ID", type=int, help="show agent detail (including eval / stability test results)")
    p.add_argument("--agent", metavar="ID", help="task agent id")
    p.add_argument("--args", metavar="JSON", default="{}",
                   help='agent args JSON, e.g. \'{"stock_code":"600519.SH"}\'')
    p.add_argument("--wait", action="store_true",
                   help="poll until the run finishes, then download + extract report.zip and print the decision")
    p.add_argument("--timeout", type=int, default=900, help="poll timeout seconds (default 900 = 15 min)")
    p.add_argument("--out-dir", metavar="DIR", default=None,
                   help="where to extract report.zip (default: ~/.finmeta/runs/agent-<id>_<time>/)")
    opts = p.parse_args()

    if opts.list:
        list_task_agents()
        return
    if opts.detail:
        show_agent_detail(opts.detail)
        return
    if not opts.agent:
        p.print_help()
        sys.exit(1)

    try:
        agent_args = json.loads(opts.args)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: --args is not valid JSON: {e}")

    print(f"→ POST /agents/{opts.agent}/a2a/  args={json.dumps(agent_args, ensure_ascii=False)}")
    resp = submit(opts.agent, agent_args)
    run_id = resp.get("run_id")
    print(json.dumps(resp, indent=2, ensure_ascii=False))
    if not run_id:
        return  # non-job-mode agent streamed directly; nothing to poll

    if not opts.wait:
        print(f"\nrun_id={run_id}  (pass --wait to poll for result, or query "
              f"GET /agents/{opts.agent}/runs?limit=1)")
        return

    print(f"\nPolling run {run_id} (timeout {opts.timeout}s, interval 30s)...", file=sys.stderr)
    r = wait_for_run(opts.agent, run_id, timeout=opts.timeout)
    print(file=sys.stderr)

    # Timeout is NOT failure — agent may still be running (some take >15 min).
    if r is None:
        print(f"⏱ TIMEOUT: run {run_id} did not finish within {opts.timeout}s — the agent "
              f"may still be running. This is NOT a failure.")
        print(f"  Re-check later:")
        print(f'    curl -s "https://fin-meta.net/api/v1/agents/{opts.agent}/runs?limit=1" \\')
        print(f'      -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN"')
        sys.exit(124)

    status = r.get("status")
    print(f"status : {status}")
    if status != "completed":
        print(f"✗ run ended with status={status} (no result produced)")
        sys.exit(1)

    # Download + extract report.zip, read the decision from it.
    report_url = (r.get("artifacts") or {}).get("report_url")
    if not report_url:
        print(f"result : {r.get('result')}  (no report_url to download)")
        sys.exit(0)
    out_dir = opts.out_dir or default_run_dir(opts.agent, r)
    print(f"  downloading + extracting report.zip → {out_dir}", file=sys.stderr)
    action, reports_dir = download_and_extract(report_url, run_id, out_dir)
    print(f"result : {action or r.get('result')}")
    print(f"report : {reports_dir}")
    print(f"         (output.json = decision, run.log = full log, <date>/ = full analysis)")
    sys.exit(0)


if __name__ == "__main__":
    main()
