#!/usr/bin/env python3.12
"""Declarative multi-step LLM pipeline — the core of multi-agent workflows.

Principle:
    Define a workflow in YAML: "step1 drafted by model A, step2 critiqued
    by model B, step3 revised by model A". Each step can reference outputs
    of earlier steps, load file content, or use inline inputs.

Usage:
    python3.12 scripts/pipeline.py pipelines/<name>.yaml
    python3.12 scripts/pipeline.py pipelines/<name>.yaml --dry  # render only

Pipeline YAML format (example):
    name: draft-review-revise
    description: model-A drafts, model-B critiques, model-A revises
    inputs:
      source_file: inputs/raw.txt
    steps:
      - name: draft
        model: gpt-4o-mini
        max_tokens: 8192
        prompt: |
          Summarize the following:
          {file:inputs/raw.txt}

      - name: critique
        model: gpt-4o
        max_tokens: 4096
        prompt: |
          Find any factual errors or omissions in this draft:
          {step:draft}

      - name: revise
        model: gpt-4o-mini
        max_tokens: 8192
        prompt: |
          Original draft:
          {step:draft}

          Critique:
          {step:critique}

          Revise the draft based on the critique.

Placeholders:
    {file:relative/path}   Load file content (relative to project root)
    {step:name}            Output of an earlier step
    {input:key}            Value from pipeline-level `inputs` dict

Output:
    runs/pipeline-<name>-<timestamp>/
        ├── pipeline.yaml          original definition (for reproducibility)
        ├── 01-<step>.md           output of each step
        ├── 01-<step>.meta.json
        └── ...
"""
import sys
import re
import json
import time
import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import call_model, extract_content, extract_reasoning_len, get_api_key

CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def get_model_cfg(model_id):
    for m in CFG["models"]:
        if m["id"] == model_id:
            return m
    return None


def render(template, file_root, step_outputs, inputs):
    """支持 {file:path} / {step:name} / {input:key} 三种占位符。"""
    out = template

    # {file:xxx}
    def replace_file(match):
        rel = match.group(1).strip()
        p = file_root / rel
        if not p.exists():
            return f"[FILE NOT FOUND: {rel}]"
        return p.read_text(encoding="utf-8")

    out = re.sub(r"\{file:([^}]+)\}", replace_file, out)

    # {step:name}
    def replace_step(match):
        name = match.group(1).strip()
        if name not in step_outputs:
            return f"[STEP NOT FOUND: {name}]"
        return step_outputs[name]

    out = re.sub(r"\{step:([^}]+)\}", replace_step, out)

    # {input:key}
    if inputs:
        def replace_input(match):
            key = match.group(1).strip()
            return str(inputs.get(key, f"[INPUT NOT FOUND: {key}]"))
        out = re.sub(r"\{input:([^}]+)\}", replace_input, out)

    return out


def run_pipeline(pipeline_path):
    pipeline = yaml.safe_load(Path(pipeline_path).read_text(encoding="utf-8"))
    name = pipeline.get("name", "unnamed")
    steps = pipeline.get("steps", [])
    inputs = pipeline.get("inputs", {})

    if not steps:
        print("[err] pipeline 没有 steps")
        sys.exit(1)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / "runs" / f"pipeline-{name}-{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 复制 pipeline 定义到 run 目录（可追溯）
    (out_dir / "pipeline.yaml").write_text(
        Path(pipeline_path).read_text(encoding="utf-8"), encoding="utf-8"
    )

    print(f"[pipeline] {name} → {out_dir.relative_to(ROOT)}")
    print(f"[pipeline] {len(steps)} steps")
    print()

    step_outputs = {}
    api_key = get_api_key(CFG)

    for i, step in enumerate(steps, 1):
        step_name = step["name"]
        model_id = step["model"]
        model_cfg = get_model_cfg(model_id)
        if not model_cfg:
            print(f"  [{i:02d}] {step_name}: 未知模型 {model_id}")
            sys.exit(1)

        prompt = render(step["prompt"], ROOT, step_outputs, inputs)
        max_tokens = step.get("max_tokens", model_cfg.get("max_output", 4096))
        temperature = step.get("temperature", CFG["defaults"]["temperature"])

        start = time.time()
        try:
            resp = call_model(
                endpoint=CFG["endpoint"],
                api_key=api_key,
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=CFG["defaults"]["timeout"],
            )
            content = extract_content(resp)
            reasoning_len = extract_reasoning_len(resp)
            elapsed = time.time() - start
            step_outputs[step_name] = content

            out_file = out_dir / f"{i:02d}-{step_name}.md"
            out_file.write_text(content, encoding="utf-8")

            meta = {
                "step": step_name,
                "model": model_id,
                "elapsed_s": round(elapsed, 2),
                "usage": resp.get("usage", {}),
                "content_chars": len(content),
                "reasoning_chars": reasoning_len,
                "prompt_chars": len(prompt),
                "ok": True,
            }
            (out_dir / f"{i:02d}-{step_name}.meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            tok = resp.get("usage", {}).get("total_tokens", "?")
            print(f"  [{i:02d}] {step_name:<14} {model_id:<12} OK   {elapsed:>6.2f}s tokens={tok}")
        except Exception as e:
            elapsed = time.time() - start
            err_msg = f"{type(e).__name__}: {e}"
            print(f"  [{i:02d}] {step_name:<14} {model_id:<12} FAIL {elapsed:>6.2f}s")
            print(f"       {err_msg}")
            (out_dir / f"{i:02d}-{step_name}.error.txt").write_text(err_msg, encoding="utf-8")
            sys.exit(2)

    print()
    print(f"[done] outputs: {out_dir.relative_to(ROOT)}")
    print(f"[next] read {out_dir.relative_to(ROOT)}/ in your editor or LLM session")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run a multi-step LLM pipeline")
    parser.add_argument("yaml_file", nargs="?", help="path to pipeline yaml")
    parser.add_argument("--dry", action="store_true",
                        help="show rendered prompts without calling models")
    args = parser.parse_args()
    if not args.yaml_file:
        print(__doc__)
        sys.exit(1)

    if args.dry:
        pipeline = yaml.safe_load(Path(args.yaml_file).read_text(encoding="utf-8"))
        inputs = pipeline.get("inputs", {})
        step_outputs = {}
        print(f"[dry] pipeline: {pipeline.get('name')}")
        print(f"[dry] {len(pipeline.get('steps', []))} steps")
        print()
        for i, step in enumerate(pipeline.get("steps", []), 1):
            for prev in pipeline["steps"][:i - 1]:
                step_outputs.setdefault(prev["name"], f"[OUTPUT OF STEP: {prev['name']}]")
            rendered = render(step["prompt"], ROOT, step_outputs, inputs)
            print(f"--- step {i:02d}: {step['name']} ({step['model']}) ---")
            print(rendered[:1500] + ("\n... [truncated]" if len(rendered) > 1500 else ""))
            print()
        return

    run_pipeline(args.yaml_file)


if __name__ == "__main__":
    main()
