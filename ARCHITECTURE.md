# Architecture & Multi-Agent Patterns

> Why this repo is shaped the way it is, and how to extend it.

## Design principles

1. **Thin scripts, no framework.** Every problem this repo solves can be
   expressed in a 50-line script. CrewAI/LangGraph/AutoGen would add a
   layer of indirection without solving anything we don't already have.
2. **Orchestrator-agnostic.** The orchestration vocabulary is plain
   shell: "run a script, read its output." Any LLM CLI tool (Claude
   Code, OpenCode, ChatGPT desktop, plain bash) can drive this repo.
3. **Isolation over integration.** Evaluation outputs land in `runs/`
   and never write to the user's knowledge base or production data.
   Any "promotion" to production is a manual, deliberate act.
4. **Reproducibility via input freezing.** Source materials are copied
   into `inputs/` as snapshots, not referenced by path. The same task
   runs identically a month later.
5. **Hallucination control by architecture, not prompt engineering.**
   Cross-model verification (`scripts/cross_check.py`) catches single-model
   hallucinations. Strong prompts are nice-to-have, not load-bearing.

## Component layers

```
┌──────────────────────────────────────────────────────────┐
│  Orchestrator (you / Claude Code / OpenCode / ChatGPT)   │
│  - decides what to evaluate                              │
│  - reads outputs from runs/                              │
│  - judges quality, makes promotion decisions             │
└──────────────────┬───────────────────────────────────────┘
                   │  shell / Bash
                   ▼
┌──────────────────────────────────────────────────────────┐
│  Workers (scripts/)                                      │
│  - ask.py        single-shot caller                      │
│  - run.py        batch task runner (parallel)            │
│  - cross_check.py multi-model verification               │
│  - pipeline.py   declarative multi-step workflow         │
│  - usage.py      LiteLLM-only budget query               │
└──────────────────┬───────────────────────────────────────┘
                   │  HTTPS POST (OpenAI-compatible)
                   ▼
┌──────────────────────────────────────────────────────────┐
│  LLM Provider (your choice)                              │
│  LiteLLM / OpenAI / Anthropic / Ollama / vLLM / etc.     │
└──────────────────────────────────────────────────────────┘
```

## Multi-agent patterns

### Pattern A: Single-shot dispatch (`ask.py`)

The simplest pattern: orchestrator hands a prompt to one worker model,
gets a response back. This is what most "ChatGPT-style" interactions are.

```sh
python3.12 scripts/ask.py gpt-4o-mini "rewrite this in plain English: ..."
```

**When to use**: low-stakes tasks, drafts, batch transformations.

### Pattern B: Parallel batch (`run.py`)

Run the same task on N models simultaneously, store outputs side by side.
Used for evaluation and for "I want to see what each model would do."

```sh
python3.12 scripts/run.py 02-meeting-summary
# → runs/<date>-NNN/{model-a,model-b,model-c}/02-meeting-summary.md
```

**When to use**: evaluation, A/B comparison, generating diverse drafts.

### Pattern C: Cross-verification (`cross_check.py`)

Run the same prompt on 2+ models, auto-extract factual clues from each
output, flag any clue that appears in only one model's output. The
orchestrator (or human) reviews the flagged differences.

```sh
python3.12 scripts/cross_check.py "Summarize Q3 financials: ..."
```

**Why this works**: a single model can hallucinate confidently. Two
independent models hallucinating the *same* fact in the same direction
is much rarer. Automatic diff focuses human attention on the
suspicious 5% rather than re-reading the whole output.

**When to use**: any time the output will be used for a real decision.
Especially good for tasks involving numbers, names, dates.

### Pattern D: Declarative pipeline (`pipeline.py`)

Multi-step workflows defined in YAML. Each step's output can feed into
the next step's prompt via `{step:name}` placeholder. The canonical
template is `draft → critique → revise`:

```yaml
steps:
  - name: draft
    model: model-a    # cheap, fast
    prompt: "Draft a summary of: {file:source.txt}"

  - name: critique
    model: model-b    # stronger, more critical
    prompt: "Find errors in this draft: {step:draft}"

  - name: revise
    model: model-a
    prompt: "Revise based on critique. Draft: {step:draft}\nCritique: {step:critique}"
```

**When to use**: any task that benefits from peer review. Three steps
catches more issues than two and is the sweet spot before diminishing
returns set in.

**Anti-pattern: agent debate.** AutoGen-style "model A and model B
argue back and forth for 5 rounds" sounds smart but burns 10x the
tokens for marginal quality gain. We don't support it.

## Where the orchestrator sits

The repo deliberately does **not** include an orchestrator. Instead,
choose one based on your workflow:

| Orchestrator | Strengths | Best for |
|---|---|---|
| **Claude Code** (CLI) | Deep judgment, lark/MCP/skill ecosystem, slash commands | Complex multi-step work, decisions, fact-checking |
| **OpenCode** (CLI) | Native subagent support, model-agnostic, Tab switching | Daily tasks, model-routing, parallel sessions |
| **ChatGPT/Claude.ai web** | UI, conversation history | Exploratory thinking, brainstorming |
| **Plain bash + cron** | Zero deps, scriptable | Scheduled batch jobs, CI |
| **Your own python script** | Full control | Custom routing logic |

### Claude Code integration

If you use Claude Code, define slash commands in `~/.claude/commands/`
to make this repo's scripts feel native:

**Example: `~/.claude/commands/ask.md`**
```markdown
---
description: Ask a configured local LLM via llm-pm-bench
---

Run `python3.12 ~/Projects/llm-pm-bench/scripts/ask.py <model> "<prompt>"`
where `<model>` and `<prompt>` are parsed from the user's input.
After the response, do a light fact-check: if the user's intent
involves numbers/dates/names, remind them to verify against source.
```

Then in your CC session: `/ask gpt-4o-mini summarize this paragraph: ...`

**Example: `~/.claude/commands/cross-check.md`**
```markdown
---
description: Cross-check a prompt across two models, summarize differences
---

Run cross_check.py and read the resulting markdown. Then synthesize
one final answer that incorporates the high-confidence parts from both
models, noting any flagged factual differences for the user.
```

### OpenCode integration

OpenCode has native subagent support. You can configure subagents in
`~/.config/opencode/agent/<name>.md`:

```markdown
---
description: Meeting summarization specialist
model: level-llm/your-best-model
mode: subagent
tools: { read: true, write: false, bash: false }
---
You specialize in turning raw meeting transcripts into structured summaries...
```

Pick the model based on this repo's evaluation results. Different
subagents can use different models — assign the strongest model to
the highest-stakes role.

## How to evaluate a new model

1. **Add it to `config.yaml`**:
   ```yaml
   models:
     - id: your-new-model
       label: Your New Model
       max_output: 8192
   ```

2. **Run all 5 tasks**:
   ```sh
   for task in 01-jargon-explanation 02-meeting-summary 03-prd-draft \
               04-design-contradiction 05-sql-debug; do
     python3.12 scripts/run.py $task
   done
   ```

3. **Read the outputs in `runs/<date>-NNN/`** side by side with your
   current model's outputs.

4. **Score against the rubric in each `tasks/*.md` frontmatter**. The
   easiest way is to give your orchestrator (Claude Code session, etc.)
   the rubric + all outputs and ask it to score, then spot-check.

5. **Decision**: if the new model wins on tasks you care about and
   loses on tasks you don't, switch. If it loses on something
   important, don't switch — even if its average score is higher.

## How to add a new task

1. Create `tasks/NN-name.md` with frontmatter:
   ```yaml
   ---
   id: NN-name
   title: Human-readable title
   inputs: {}    # or {key: value} pairs for {key} substitution
   rubric:
     - dimension: Accuracy
       weight: 0.4
       desc: ...
   ---
   ```
2. Body is the prompt template. Use `{file:relative/path}` to load files,
   `{key}` to substitute inputs.
3. Add source materials to `inputs/NN-name/` if needed.
4. Test rendering without burning tokens:
   ```sh
   python3.12 scripts/run.py NN-name --dry
   ```
5. Run for real:
   ```sh
   python3.12 scripts/run.py NN-name
   ```

## How to extend `scripts/`

Keep each script focused. The current scripts are:
- `lib.py`: shared HTTP client, env loading, frontmatter parsing
- `ask.py`: 1-prompt-1-model
- `run.py`: 1-prompt-N-models
- `cross_check.py`: 1-prompt-N-models + diff
- `pipeline.py`: declarative chain
- `usage.py`: LiteLLM budget (provider-specific)

If you need to add a new pattern (e.g., a `vote.py` that runs the same
prompt 5 times and takes the most common answer), follow the same
shape: a thin script that imports from `lib.py`, accepts CLI args,
writes outputs to `runs/`, prints a summary to stdout.

**Keep it under 250 lines.** If a script grows beyond that, it's doing
too much.

## What's NOT in scope

- Web UI / dashboard
- Database / persistent state
- Auth / multi-user support
- Streaming responses (would complicate `run.py` parallelism)
- Fine-tuning / training infrastructure
- RAG / vector store integration (use external tooling for this)
- Statistical significance tests (too few samples to matter)

If you need any of the above, you've outgrown this repo. Look at:
- **lm-eval-harness** for academic-style benchmarks
- **LangGraph** for stateful multi-agent workflows
- **Promptfoo** for prompt regression testing with web UI
- **Inspect AI** (UK AISI) for safety evaluation
