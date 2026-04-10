#!/usr/bin/env python3.12
"""Generic LLM caller — the foundation of multi-agent orchestration.

Usage:
    python3.12 scripts/ask.py <model_id> "<prompt>"
    echo "<prompt>" | python3.12 scripts/ask.py <model_id>
    python3.12 scripts/ask.py <model_id> --file path/to/prompt.md
    python3.12 scripts/ask.py <model_id> "<prompt>" --system "<system msg>"
    python3.12 scripts/ask.py <model_id> "<prompt>" --json   # full response JSON
    python3.12 scripts/ask.py --list                         # list available models

Design intent:
    A one-liner to invoke any configured model. Stdout is plain text, ideal
    for shell pipes or being called by an upstream orchestrator (Claude Code,
    OpenCode, scripts):
        python3.12 scripts/ask.py kimi "summarize: ..." | grep ...
        python3.12 scripts/ask.py qwen --file draft.md > critique.md

Exit codes:
    0 = success
    1 = bad arguments or unknown model
    2 = API call failed
"""
import sys
import json
import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import call_model, extract_content, get_api_key

CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def list_models():
    print("Available models:")
    for m in CFG["models"]:
        print(f"  {m['id']:<14} {m.get('label', '')}")
    print()
    print(f"endpoint: {CFG['endpoint']}")


def get_model_cfg(model_id):
    for m in CFG["models"]:
        if m["id"] == model_id:
            return m
    return None


def main():
    parser = argparse.ArgumentParser(
        description="通用 LLM 调用器", add_help=False
    )
    parser.add_argument("model", nargs="?", help="model id (e.g. gpt-4o-mini)")
    parser.add_argument("prompt", nargs="?", help="prompt 文本（也可用 stdin 或 --file）")
    parser.add_argument("--system", help="system message", default=None)
    parser.add_argument("--file", help="从文件读 prompt", default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--json", action="store_true", help="输出完整 response JSON")
    parser.add_argument("--list", action="store_true", help="列出可用模型")
    parser.add_argument("-h", "--help", action="store_true")

    args = parser.parse_args()

    if args.help or (not args.model and not args.list):
        print(__doc__)
        sys.exit(0 if args.help else 1)

    if args.list:
        list_models()
        sys.exit(0)

    model_cfg = get_model_cfg(args.model)
    if not model_cfg:
        print(f"[err] 未知模型: {args.model}", file=sys.stderr)
        list_models()
        sys.exit(1)

    # 解析 prompt: --file > positional > stdin
    if args.file:
        prompt = Path(args.file).read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read()
    else:
        print("[err] 缺少 prompt（用位置参数 / --file / stdin 三种之一）", file=sys.stderr)
        sys.exit(1)

    # 构造 messages
    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = call_model(
            endpoint=CFG["endpoint"],
            api_key=get_api_key(CFG),
            model=args.model,
            messages=messages,
            max_tokens=args.max_tokens or model_cfg.get("max_output", 4096),
            temperature=args.temperature if args.temperature is not None
                        else CFG["defaults"]["temperature"],
            timeout=CFG["defaults"]["timeout"],
        )
    except Exception as e:
        print(f"[err] API 调用失败: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    else:
        print(extract_content(resp))


if __name__ == "__main__":
    main()
