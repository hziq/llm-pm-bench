#!/usr/bin/env python3.12
"""API 调用封装：调本地 LLM endpoint，OpenAI 兼容范式。"""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path


def load_env(env_file=None):
    """加载 .env 文件到 os.environ（已存在的不覆盖）。返回 dict。"""
    if env_file is None:
        env_file = Path(__file__).resolve().parent.parent / ".env"
    else:
        env_file = Path(env_file)
    if not env_file.exists():
        return {}
    loaded = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        loaded[k] = v
        os.environ.setdefault(k, v)
    return loaded


def get_api_key(cfg):
    """Resolve API key from config:
    - cfg.api_key (direct value, NOT recommended for git-tracked configs)
    - cfg.api_key_env (env var name, default: LLM_API_KEY)
    Loads .env file automatically.
    """
    if "api_key" in cfg and cfg["api_key"]:
        return cfg["api_key"]
    env_name = cfg.get("api_key_env", "LLM_API_KEY")
    load_env()  # auto-load .env if present
    key = os.environ.get(env_name)
    if not key:
        raise RuntimeError(
            f"API key not set. Set {env_name}=... in .env file, or "
            f"set api_key in config.yaml. See .env.example for reference."
        )
    return key


def call_model(endpoint, api_key, model, messages,
               max_tokens=4096, temperature=0.3, timeout=180, retries=1):
    """调用 OpenAI 兼容的 chat completions endpoint。返回完整 response dict。

    带 retries 次重试（默认 1 次），网络抖动友好。
    """
    import time as _time
    url = f"{endpoint}/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            last_err = e
            if attempt < retries:
                _time.sleep(2 ** attempt)  # 1s, 2s, 4s 退避
                continue
            raise
    raise last_err  # 不应到达


def extract_content(resp):
    """Extract text from a chat completion response.
    Falls back to reasoning_content for models that put truncated answers there."""
    msg = resp["choices"][0]["message"]
    return msg.get("content") or msg.get("reasoning_content") or ""


def extract_reasoning_len(resp):
    """Return the character length of the reasoning_content field.
    Reasoning models (e.g. o1, DeepSeek R1, some Qwen variants) produce
    large 'thinking' traces that are billed as completion tokens but not
    shown in the regular content field. Track this for cost awareness."""
    msg = resp["choices"][0]["message"]
    reasoning = msg.get("reasoning_content") or ""
    if not reasoning and msg.get("content"):
        # Some providers put reasoning in provider_specific_fields
        psf = msg.get("provider_specific_fields") or {}
        reasoning = psf.get("reasoning_content") or psf.get("reasoning") or ""
    return len(reasoning)


def parse_frontmatter(text):
    """Parse YAML frontmatter from a markdown file.
    Returns (meta_dict, body_str). If no frontmatter, returns ({}, text).
    """
    import yaml
    if not text.startswith("---\n"):
        return {}, text.strip()
    try:
        end = text.index("\n---\n", 4)
    except ValueError:
        return {}, text.strip()
    meta = yaml.safe_load(text[4:end]) or {}
    body = text[end + 5:].strip()
    return meta, body
