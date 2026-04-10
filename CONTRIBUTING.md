# Contributing

Thanks for your interest. This project is intentionally minimal — please
keep contributions in the same spirit.

## Project Philosophy

- **Thin scripts over frameworks.** No CrewAI / LangGraph / AutoGen.
  If a 50-line python script can do it, that's the right tool.
- **Orchestration belongs to the human or to a CLI tool (Claude Code,
  OpenCode, ChatGPT).** This repo provides workers, not orchestrators.
- **Isolation over integration.** Evaluation outputs never write to a
  user's knowledge base. The boundary is enforced by directory structure.
- **Real tasks over synthetic benchmarks.** PM/SRE/data work, not GSM8K.

## What's Welcome

- 🆕 **New task templates** in your domain (legal? sales? UX research?)
  PRs that add a new `tasks/NN-domain-name.md` + matching `inputs/` are
  the highest-value contributions.
- 🐛 **Bug fixes** in scripts.
- 📖 **Translations** of README / ARCHITECTURE.
- 🧪 **Smoke tests** in `tests/` (none exist yet).

## What's Not Welcome

- ❌ Refactoring to use a multi-agent framework.
- ❌ Adding a web UI / dashboard / database.
- ❌ Adding ML / training code. This is an *evaluation* tool, not a
  training tool.

## Local Dev

```sh
git clone https://github.com/hziq/llm-pm-bench
cd llm-pm-bench
cp .env.example .env
# edit .env with your API key
python3.12 scripts/ask.py --list
```

## Code Style

- Python 3.10+, no external deps beyond `pyyaml` (which most envs have).
- Stick to stdlib (`urllib` for HTTP, no `requests`).
- Comments and docstrings in English.
- Keep each script < 250 lines.

## Adding a Task

1. Create `tasks/NN-name.md` with YAML frontmatter (`id`, `title`,
   `inputs`, `rubric`) and a prompt body.
2. If the task needs source material, add it to `inputs/NN-name/` and
   reference with `{file:inputs/NN-name/something.md}`.
3. Test with `--dry`:
   ```sh
   python3.12 scripts/run.py NN-name --dry
   ```
4. Run for real and capture results in `runs/`.
5. Submit a PR with the task file + a one-paragraph description of why
   it's a useful evaluation scenario.
