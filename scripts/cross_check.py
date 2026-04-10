#!/usr/bin/env python3.12
"""Cross-check a prompt across multiple models — hallucination control tool.

Principle:
    Send the same prompt to N models in parallel, present outputs side by
    side, and auto-extract "factual clues" (numbers, dates, quoted phrases,
    acronyms) that appear in only one model's output. Any single-model
    hallucination is exposed by the other model(s). Final judgment is left
    to a human reviewer (or an upstream LLM orchestrator like Claude Code).

Usage:
    python3.12 scripts/cross_check.py "<prompt>"
    python3.12 scripts/cross_check.py --file path/to/prompt.md
    python3.12 scripts/cross_check.py --task 03-prd-draft
    python3.12 scripts/cross_check.py "..." --models model-a,model-b
    python3.12 scripts/cross_check.py "..." --out runs/crosscheck-X.md

Output:
    A markdown file (also stdout unless --quiet) saved to
    runs/crosscheck-<timestamp>.md, containing:
    - the prompt
    - each model's full output
    - auto-extracted "factual clues" that need human verification

Known limitations:
    - Factual clue extraction does not skip code blocks, so SQL/code numbers
      may be flagged as differences. Filter manually.
"""
import sys
import re
import json
import argparse
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import call_model, extract_content, get_api_key, parse_frontmatter

CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
# Default to the first 2 models in config.yaml. Override with --models.
DEFAULT_MODELS = [m["id"] for m in CFG.get("models", [])[:2]]


def get_model_cfg(model_id):
    for m in CFG["models"]:
        if m["id"] == model_id:
            return m
    return None


def call_one(model_id, prompt):
    """调单个模型，返回 (model_id, content, error)。"""
    cfg = get_model_cfg(model_id)
    if not cfg:
        return model_id, None, f"unknown model: {model_id}"
    try:
        resp = call_model(
            endpoint=CFG["endpoint"],
            api_key=get_api_key(CFG),
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=cfg.get("max_output", 4096),
            temperature=CFG["defaults"]["temperature"],
            timeout=CFG["defaults"]["timeout"],
        )
        return model_id, extract_content(resp), None
    except Exception as e:
        return model_id, None, f"{type(e).__name__}: {e}"


def extract_factual_clues(text):
    """从一段文本里抽出"事实线索"——数字、引号内短语、全大写词、日期。
    用于人工对比时聚焦关键差异。"""
    clues = set()
    # 数字（含小数、百分号、单位）
    for m in re.finditer(r"\b\d+(?:\.\d+)?[%kKmM万千百]?\b", text):
        clues.add(m.group())
    # 中英文引号内短语
    for m in re.finditer(r"['\"\u201c\u201d\u2018\u2019“”‘’](.{1,20}?)['\"\u201c\u201d\u2018\u2019“”‘’]", text):
        clues.add(m.group(1).strip())
    # 全大写词（>=2 字符的英文缩写）
    for m in re.finditer(r"\b[A-Z]{2,}\b", text):
        clues.add(m.group())
    # 日期格式
    for m in re.finditer(r"\b\d{4}[-./]\d{1,2}(?:[-./]\d{1,2})?\b", text):
        clues.add(m.group())
    return clues


def make_report(prompt, results):
    """results: [(model, content, error)]"""
    lines = []
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"# Cross-check Report — {ts}")
    lines.append("")
    lines.append("## Prompt")
    lines.append("")
    lines.append("```")
    lines.append(prompt[:2000] + ("\n... [truncated]" if len(prompt) > 2000 else ""))
    lines.append("```")
    lines.append("")

    # Per-model outputs
    for model, content, err in results:
        lines.append(f"## {model}")
        lines.append("")
        if err:
            lines.append(f"❌ **Failed**: {err}")
        else:
            lines.append(content or "[empty response]")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Factual clue diff
    ok_results = [(m, c) for m, c, e in results if c]
    if len(ok_results) >= 2:
        clue_sets = {m: extract_factual_clues(c) for m, c in ok_results}
        common = set.intersection(*clue_sets.values())
        unique = {}
        for m, clues in clue_sets.items():
            only_here = clues - common
            if only_here:
                unique[m] = sorted(only_here)

        lines.append("## ⚠️ Factual clues needing human verification")
        lines.append("")
        lines.append(f"- Clues that appeared in ALL models: {len(common)}")
        lines.append(f"- Clues that appeared in only ONE model: {sum(len(v) for v in unique.values())}")
        lines.append("")
        if unique:
            lines.append("**Clues unique to a single model (possible hallucination, or the others missed it)**:")
            lines.append("")
            for m, only in unique.items():
                lines.append(f"- **{m}** unique: {', '.join(only[:30])}")
            lines.append("")
            lines.append("> ⚠️ This is NOT automatic hallucination detection. Differences may come")
            lines.append("> from hallucination OR from one model being more thorough. Verify against source.")
            lines.append("> Note: factual clue extraction does not skip code blocks; SQL/code numbers")
            lines.append("> may be flagged. Filter manually.")
        else:
            lines.append("✅ All models agree on factual clues (still recommended to spot-check)")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Cross-check 多模型对比")
    parser.add_argument("prompt", nargs="?", help="prompt 文本")
    parser.add_argument("--file", help="从文件读 prompt")
    parser.add_argument("--task", help="跑某个 task 文件（自动渲染 inputs）")
    parser.add_argument(
        "--models", default=",".join(DEFAULT_MODELS),
        help=f"逗号分隔模型 id（默认 {','.join(DEFAULT_MODELS)}）"
    )
    parser.add_argument("--out", help="输出文件路径（默认自动生成）")
    parser.add_argument("--quiet", action="store_true", help="不打印到 stdout")
    args = parser.parse_args()

    # 解析 prompt
    if args.task:
        # 复用 run.py 的 render
        from run import render_prompt
        task_file = ROOT / "tasks" / f"{args.task}.md"
        if not task_file.exists():
            print(f"[err] task 不存在: {task_file}")
            sys.exit(1)
        meta, body = parse_frontmatter(task_file.read_text(encoding="utf-8"))
        prompt = render_prompt(body, meta.get("inputs") or {})
    elif args.file:
        prompt = Path(args.file).read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    models = [m.strip() for m in args.models.split(",") if m.strip()]

    print(f"[cross-check] prompt={len(prompt)} chars  models={','.join(models)}", file=sys.stderr)
    print(file=sys.stderr)

    # 并发跑
    results = []
    with ThreadPoolExecutor(max_workers=len(models)) as ex:
        futures = [ex.submit(call_one, m, prompt) for m in models]
        for f in futures:
            r = f.result()
            results.append(r)
            tag = "OK  " if r[1] else "FAIL"
            print(f"  [{tag}] {r[0]}", file=sys.stderr)

    # 按 models 顺序排序
    order = {m: i for i, m in enumerate(models)}
    results.sort(key=lambda x: order.get(x[0], 99))

    report = make_report(prompt, results)

    # 写文件
    if args.out:
        out_path = Path(args.out)
    else:
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        runs_dir = ROOT / "runs"
        runs_dir.mkdir(exist_ok=True)
        out_path = runs_dir / f"crosscheck-{ts}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\n[done] {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}", file=sys.stderr)

    if not args.quiet:
        print(report)


if __name__ == "__main__":
    main()
