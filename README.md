# llm-pm-bench

[English](README.md) | [中文](README_zh.md) · MIT License · No frameworks · Bring your own LLM

A minimal "thin scripts + Claude Code orchestration" toolkit for evaluating
**which LLM can replace the one you're currently using** on your real
day-to-day tasks. Built for product managers, SREs, analysts, and
solo developers who don't have time for a 200-question MMLU run but want
**half-hour, 5-real-task** answers.

## What problem does this solve

> "Can our self-hosted Kimi/GLM/Llama actually replace my Claude/ChatGPT
> subscription for the work I do every day?"

Existing benchmarks (MMLU, HumanEval, GSM8K) measure things you don't
care about. Existing multi-agent frameworks (CrewAI, LangGraph, AutoGen)
require learning a new mental model.

This repo gives you:
- **5 real-work task templates** (jargon explanation, meeting summary,
  PRD draft, design contradiction analysis, SQL debugging) you can adapt
  to your domain
- **Parallel multi-model runner** with reproducible inputs
- **Cross-model verification** to catch hallucinations by architecture, not luck
- **Declarative pipelines** for "model-A drafts → model-B critiques → model-A
  revises" workflows
- **Claude Code / OpenCode integration** via slash commands (optional)

Total: ~900 lines of Python, no framework, no database, no web UI.

## Quick start

```sh
git clone https://github.com/hziq/llm-pm-bench
cd llm-pm-bench
cp .env.example .env
# edit .env with your API key

# point config.yaml at your provider (OpenAI / LiteLLM / Ollama / vLLM / ...)
$EDITOR config.yaml

# verify connection
python3.12 scripts/ask.py --list
python3.12 scripts/ask.py gpt-4o-mini "say hi"

# run the first task across all configured models
python3.12 scripts/run.py 01-jargon-explanation

# look at the outputs (one folder per model)
ls runs/
```

## What you get

```
llm-pm-bench/
├── README.md / README_zh.md      # this file (EN/ZH)
├── ARCHITECTURE.md               # design rationale + multi-agent patterns
├── CONTRIBUTING.md               # what's welcome / what's not
├── LICENSE                       # MIT
├── config.yaml                   # endpoint + models + defaults
├── .env.example                  # API key template
├── scripts/
│   ├── lib.py                    # API + env loading + frontmatter parsing
│   ├── ask.py                    # one-shot caller (multi-agent foundation)
│   ├── run.py                    # batch task runner (parallel across models)
│   ├── cross_check.py            # multi-model parallel + factual diff
│   ├── pipeline.py               # declarative multi-step workflow
│   └── usage.py                  # LiteLLM-only: budget query
├── tasks/                        # 5 example task templates
│   ├── 01-jargon-explanation.md       # short output, strong constraint
│   ├── 02-meeting-summary.md          # long input, structured output
│   ├── 03-prd-draft.md                # instruction following + long output
│   ├── 04-design-contradiction.md     # reasoning across two documents
│   └── 05-sql-debug.md                # code generation + domain reasoning
├── inputs/                       # example source materials (mock)
├── pipelines/
│   └── draft-review-revise.yaml  # canonical 3-step pipeline
├── reports/
│   └── _template.md              # report skeleton
└── runs/                         # outputs land here (gitignored)
```

## The 5 example tasks

| # | Task | What it tests | Why it matters |
|---|---|---|---|
| 01 | Jargon explanation | Domain knowledge, short output, strict constraints | Quickest signal for "does this model know my field" |
| 02 | Meeting summary | Long-context, structured output | Real PM/manager workflow |
| 03 | PRD draft | Instruction following, long generation, judgment | Tests "useful starting point" vs "generic template" |
| 04 | Design contradiction | Reasoning across two long documents | Tests whether the model can hold 2 things in mind |
| 05 | SQL debug | Code generation + domain understanding + safety rules | Reveals whether the model fabricates field names or hallucinates "results" |

**These are templates.** Adapt them to your domain — replace
`inputs/02-meeting/transcript.txt` with your own meeting, edit
`tasks/02-meeting-summary.md` rubric to match what you care about.

## Core concepts

### Orchestrator vs workers
The orchestrator (you, ChatGPT, Claude Code, OpenCode) decides what to
evaluate, judges results, and makes final calls. The scripts in
`scripts/` are **workers** — they execute the API calls and record outputs.
This separation is intentional: any LLM CLI tool can be the orchestrator,
no framework needed.

### Hallucination control by architecture
Don't rely on prompt engineering alone. Use **cross-model verification**:
send the same prompt to 2-3 models in parallel and let your orchestrator
diff the outputs. Single-model hallucinations get exposed.

```sh
python3.12 scripts/cross_check.py "Summarize this document: ..."
# → runs/crosscheck-<timestamp>.md with side-by-side outputs +
#   auto-extracted "factual clues that need human verification"
```

### Isolation principle
Evaluation outputs (`runs/`) **never** write to your knowledge base or
production data. If you want to promote an output, you do it manually.
This prevents hallucinated content from contaminating downstream work.

### No framework
No CrewAI, no LangGraph, no AutoGen. The entire orchestration vocabulary
is: "run a script, read its output, decide what to do next." If your
workflow grows beyond what 250-line scripts can handle, you've outgrown
this repo and should look at LangGraph.

## Optional: Claude Code integration

If you use [Claude Code](https://www.anthropic.com/claude-code) as your
CLI orchestrator, you can install slash commands to call this repo:

```sh
# example commands available (define them in ~/.claude/commands/):
#   /ask <model> <prompt>          → wraps scripts/ask.py
#   /cross-check <prompt>          → wraps scripts/cross_check.py
#   /pipeline <name>               → wraps scripts/pipeline.py
```

See `ARCHITECTURE.md` for details and example command files.

## Optional: OpenCode integration

[OpenCode](https://opencode.ai) has native subagent support. You can
configure subagents to use the same models you've evaluated here. See
`ARCHITECTURE.md` § "OpenCode integration".

## When to use this repo / when not to

**✅ Use it when:**
- You want to compare 2-5 LLMs on tasks you actually do
- You want to know if a self-hosted model can replace a paid API
- You're a solo developer / PM / analyst and don't want to learn a framework
- You want hallucination control without paying for ground truth

**❌ Don't use it when:**
- You need rigorous statistical evaluation (use `lm-eval-harness`)
- You need to evaluate 100+ tasks (use a real benchmark)
- You need fine-tuning, RAG, or training infra
- You need a web dashboard for non-technical stakeholders

## Provider compatibility

Tested with:
- ✅ LiteLLM proxy (any model behind it)
- ✅ OpenAI API
- ✅ Self-hosted vLLM
- ✅ Self-hosted Ollama (use `endpoint: http://localhost:11434/v1` and `api_key: ollama`)
- ⚠️ Anthropic API directly: needs LiteLLM in front (script uses OpenAI-compatible payload)

`scripts/usage.py` only works with LiteLLM-compatible gateways.

## Acknowledgments

Born out of evaluating 3 self-hosted Chinese models (Kimi K2.5, GLM-5,
Qwen 3.5) against Claude Opus 4.6 for daily PM work in industrial APS/MES
software. The original eval found that Kimi K2.5 was sometimes *better*
than Claude on Chinese-domain short-output tasks — a result worth open-sourcing
the methodology for.

## License

[MIT](LICENSE)
