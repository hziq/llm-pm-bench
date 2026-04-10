#!/usr/bin/env python3.12
"""Run one task across all (or selected) configured models.

Outputs land in runs/<date>-<seq>/<model>/<task>.md (+ .meta.json).

Usage:
    python3.12 scripts/run.py <task_id>
    python3.12 scripts/run.py <task_id> --dry            # render prompt only
    python3.12 scripts/run.py <task_id> --n 3            # run 3 times for averaging
    python3.12 scripts/run.py <task_id> --models a,b     # only run specific models

Example:
    python3.12 scripts/run.py 01-jargon-explanation
"""
import sys
import json
import time
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

# 让脚本无论从哪跑都能找到工程根
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import call_model, extract_content, extract_reasoning_len, parse_frontmatter, get_api_key

CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
# API key is loaded lazily inside main() so --dry can work without one


def render_prompt(template, inputs):
    """占位符替换。支持:
    - {key}: 直接替换。list 渲染为 bullet 列表，其它转字符串
    - {file:相对路径}: 加载文件内容（相对于工程根 ROOT）
    """
    import re

    out = template

    # 1) {file:xxx} 文件加载（先处理）
    def replace_file(match):
        rel_path = match.group(1).strip()
        file_path = ROOT / rel_path
        if not file_path.exists():
            return f"[FILE NOT FOUND: {rel_path}]"
        return file_path.read_text(encoding="utf-8")

    out = re.sub(r"\{file:([^}]+)\}", replace_file, out)

    # 2) {key} 普通占位符
    if inputs:
        for key, val in inputs.items():
            placeholder = "{" + key + "}"
            if isinstance(val, list):
                rendered = "\n".join(f"- {item}" for item in val)
            else:
                rendered = str(val)
            out = out.replace(placeholder, rendered)

    return out


def run_one(model_cfg, prompt, run_dir, task_id):
    """跑单个模型，写 .md 和 .meta.json，返回 meta dict。"""
    model_id = model_cfg["id"]
    out_dir = run_dir / model_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{task_id}.md"
    meta_file = out_dir / f"{task_id}.meta.json"

    start = time.time()
    try:
        resp = call_model(
            endpoint=CFG["endpoint"],
            api_key=get_api_key(CFG),
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=model_cfg.get("max_output", 4096),
            temperature=CFG["defaults"]["temperature"],
            timeout=CFG["defaults"]["timeout"],
        )
        content = extract_content(resp)
        reasoning_len = extract_reasoning_len(resp)
        elapsed = time.time() - start
        out_file.write_text(content, encoding="utf-8")
        meta = {
            "model": model_id,
            "task": task_id,
            "elapsed_s": round(elapsed, 2),
            "usage": resp.get("usage", {}),
            "content_chars": len(content),
            "reasoning_chars": reasoning_len,
            "ok": True,
        }
    except Exception as e:
        elapsed = time.time() - start
        out_file.write_text(f"[ERROR] {type(e).__name__}: {e}", encoding="utf-8")
        meta = {
            "model": model_id,
            "task": task_id,
            "elapsed_s": round(elapsed, 2),
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
        }
    meta_file.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def main():
    import argparse
    parser = argparse.ArgumentParser(description="跑一个 task 在所有模型上")
    parser.add_argument("task_id", help="task id (例 01-business-terms)")
    parser.add_argument("--dry", action="store_true",
                        help="只渲染 prompt 不调 API（看输入长啥样）")
    parser.add_argument("--n", type=int, default=1,
                        help="同 prompt 跑几次取多次（默认 1）")
    parser.add_argument("--models", default=None,
                        help="只跑指定模型（逗号分隔），默认全部")
    args = parser.parse_args()

    task_id = args.task_id
    task_file = ROOT / "tasks" / f"{task_id}.md"
    if not task_file.exists():
        print(f"[ERR] task not found: {task_file}")
        sys.exit(1)

    meta, template = parse_frontmatter(task_file.read_text(encoding="utf-8"))
    prompt = render_prompt(template, meta.get("inputs", {}))

    # dry-run 模式：只看 prompt
    if args.dry:
        print(f"[dry] task={task_id} prompt={len(prompt)} chars")
        print(f"[dry] inputs={list((meta.get('inputs') or {}).keys())}")
        print(f"[dry] rubric dimensions={len(meta.get('rubric') or [])}")
        print()
        print("=== rendered prompt ===")
        print(prompt[:3000])
        if len(prompt) > 3000:
            print(f"\n... [truncated, full length {len(prompt)}]")
        return

    # 决定模型清单
    all_models = CFG["models"]
    if args.models:
        wanted = {m.strip() for m in args.models.split(",")}
        models_to_run = [m for m in all_models if m["id"] in wanted]
        if not models_to_run:
            print(f"[ERR] 没有匹配的模型: {wanted}")
            sys.exit(1)
    else:
        models_to_run = all_models

    # 计算 run_dir
    date = datetime.date.today().isoformat()
    runs_root = ROOT / "runs"
    runs_root.mkdir(exist_ok=True)
    n_seq = 1
    while (runs_root / f"{date}-{n_seq:03d}").exists():
        n_seq += 1
    run_dir = runs_root / f"{date}-{n_seq:03d}"
    run_dir.mkdir()

    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    (run_dir / "task_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[run] task={task_id} -> {run_dir.relative_to(ROOT)}")
    print(f"[run] prompt 长度: {len(prompt)} chars")
    print(f"[run] 模型: {[m['id'] for m in models_to_run]}")
    if args.n > 1:
        print(f"[run] 多次跑测: 每个模型跑 {args.n} 次")
    print()

    # 跑测：每个 (model, run_idx) 组合
    results = []
    work_items = []
    for m in models_to_run:
        for run_idx in range(args.n):
            # 多次时给 task_id 加 .Nx 后缀，区分文件
            suffix = "" if args.n == 1 else f".{run_idx + 1}"
            work_items.append((m, prompt, run_dir, task_id + suffix))

    with ThreadPoolExecutor(max_workers=min(len(work_items), 6)) as ex:
        futures = [ex.submit(run_one, *item) for item in work_items]
        for f in as_completed(futures):
            r = f.result()
            tag = "OK  " if r["ok"] else "FAIL"
            usage = r.get("usage", {})
            tok = usage.get("total_tokens", "?")
            print(f"  [{tag}] {r['model']:<12} {r['task']:<25} {r['elapsed_s']:>6.2f}s  tokens={tok}")
            if not r["ok"]:
                print(f"         {r['error']}")
            results.append(r)

    print()
    print(f"[done] outputs: {run_dir.relative_to(ROOT)}")
    print(f"[next] CC 会话内：")
    print(f"       1) 读 {run_dir.relative_to(ROOT)}/prompt.md")
    print(f"       2) 生成 claude-baseline/{task_id}.md")
    print(f"       3) 读 4 套产出，按 task rubric 打分，写 reports/{run_dir.name}.md")


if __name__ == "__main__":
    main()
