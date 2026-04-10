#!/usr/bin/env python3.12
"""Query LLM gateway key usage / budget.

⚠️  PROVIDER-SPECIFIC: This script targets a LiteLLM-compatible
`/internal/key-usage` endpoint. It works out of the box with:
  - LiteLLM Proxy (https://docs.litellm.ai)
  - Compatible self-hosted gateways

For other providers (OpenAI, Anthropic, Gemini directly), you'll need
to either disable this script or adapt the URL/response shape.
Configure the endpoint via `usage_endpoint` in config.yaml.

Usage:
    python3.12 scripts/usage.py              # print current balance
    python3.12 scripts/usage.py --history    # append to usage_history.csv
    python3.12 scripts/usage.py --json       # raw JSON
"""
import sys
import json
import urllib.request
import datetime
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import get_api_key
import yaml

CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
USAGE_URL = CFG.get("usage_endpoint")  # e.g. https://your-gateway/internal/key-usage
HISTORY_FILE = ROOT / "usage_history.csv"


def fetch():
    if not USAGE_URL:
        raise RuntimeError(
            "usage_endpoint not configured in config.yaml. "
            "This script only works with LiteLLM-compatible gateways. "
            "Set `usage_endpoint: https://your-gateway/internal/key-usage` to enable."
        )
    api_key = get_api_key(CFG)
    req = urllib.request.Request(
        USAGE_URL, headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def fmt(data):
    used_pct = data.get("budget_used_percent", 0)
    remaining = data.get("remaining_budget", 0)
    spend = data.get("spend", 0)
    budget = data.get("max_budget", 0)
    print()
    print(f"  Key:        {data.get('key_name', '?')}  ({data.get('key_alias', '')})")
    print(f"  Budget:     ${budget:.2f}")
    print(f"  Spent:      ${spend:.4f}")
    print(f"  Remaining:  ${remaining:.4f}")
    print(f"  Usage:      {used_pct:.2f}%")
    print()
    if used_pct >= 80:
        print(f"  ⚠️  Less than 20% budget left. Consider topping up.")
    elif used_pct >= 50:
        print(f"  ℹ️  Over half used.")
    else:
        print(f"  ✅ Healthy.")
    print()


def append_history(data):
    HISTORY_FILE.touch(exist_ok=True)
    is_new = HISTORY_FILE.stat().st_size == 0
    with HISTORY_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp", "spend", "remaining", "used_pct"])
        w.writerow([
            datetime.datetime.now().isoformat(timespec="seconds"),
            f"{data.get('spend', 0):.6f}",
            f"{data.get('remaining_budget', 0):.6f}",
            f"{data.get('budget_used_percent', 0):.4f}",
        ])
    print(f"[history] appended to {HISTORY_FILE.relative_to(ROOT)}")


def main():
    args = sys.argv[1:]
    try:
        data = fetch()
    except Exception as e:
        print(f"[err] query failed: {type(e).__name__}: {e}")
        sys.exit(1)

    if "--json" in args:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    fmt(data)

    if "--history" in args:
        append_history(data)


if __name__ == "__main__":
    main()
