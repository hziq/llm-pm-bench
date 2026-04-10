# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — 2026-04-10

Initial public release.

### Added
- `scripts/lib.py` — shared HTTP client (urllib-based, no `requests` dep), `.env` loader, YAML frontmatter parser, 1-retry `call_model`
- `scripts/ask.py` — single-shot model caller, the foundation for multi-agent orchestration
- `scripts/run.py` — parallel task runner across N configured models; supports `--dry`, `--n` (averaging), `--models` (filtering)
- `scripts/cross_check.py` — multi-model cross-verification with factual-clue diff extraction (for hallucination control)
- `scripts/pipeline.py` — declarative multi-step YAML pipelines with `{file:}`, `{step:}`, `{input:}` placeholders
- `scripts/usage.py` — LiteLLM-compatible budget query (optional, provider-specific)
- 5 example task templates covering jargon explanation, meeting summarization, PRD drafting, design contradiction analysis, SQL debugging
- Mock source materials in `inputs/` (SRE rate-limiting meeting, e-commerce soft delete requirement, inventory architecture contradiction, shipment debug scenario)
- `pipelines/draft-review-revise.yaml` — canonical 3-step "draft → critique → revise" template
- `reports/_template.md` — report skeleton
- Bilingual README (English + Chinese)
- `ARCHITECTURE.md` — design rationale, multi-agent patterns, Claude Code / OpenCode integration
- `CONTRIBUTING.md` — what's welcome, what's not
- MIT License

### Design principles locked in
- Thin scripts, no framework (CrewAI / LangGraph / AutoGen explicitly out of scope)
- Orchestrator-agnostic (works with Claude Code, OpenCode, ChatGPT, plain bash)
- Isolation over integration (evaluation outputs never write to user's knowledge base)
- Reproducibility via input freezing (source materials as snapshots, not path references)
- Hallucination control by architecture, not prompt engineering
- Total code < 1100 lines of Python, no dependencies beyond `pyyaml`

### Origin
This repo was forked from an internal evaluation tool used to compare
self-hosted Chinese LLMs (Kimi K2.5, GLM-5, Qwen 3.5) against Claude
Opus 4.6 for product manager work in industrial APS/MES software. The
original evaluation found that Kimi K2.5 was sometimes *better* than
Claude on Chinese-domain short-output tasks — a result worth
open-sourcing the methodology for. All company-specific materials
have been replaced with mock scenarios.
