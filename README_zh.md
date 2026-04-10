# llm-pm-bench

[English](README.md) | [中文](README_zh.md) · MIT License · 不引入框架 · 自带 LLM

一个极简的"薄脚本 + Claude Code 编排"评测工具，**用于判断哪个 LLM 能替代你正在用的那个 LLM** 来完成你日常的真实工作。面向产品经理、SRE、分析师和单兵开发者——没时间跑 200 题的 MMLU，但希望**半小时跑完 5 个真实任务**就能拿到结论。

## 它解决什么问题

> "公司自部署的 Kimi/GLM/Llama 真的能替代我每月付费的 Claude/ChatGPT 吗？"

现有 benchmark（MMLU、HumanEval、GSM8K）测的都是你不在乎的东西。现有 multi-agent 框架（CrewAI、LangGraph、AutoGen）需要你学一套新的心智模型。

这个仓库给你：
- **5 个真实工作的 task 模板**（术语解释、会议纪要、PRD 草稿、设计矛盾分析、SQL 排查），可适配到你自己的领域
- **多模型并发跑测**，输入冻结可复现
- **跨模型交叉验证**，通过架构控制幻觉而不是靠运气
- **声明式 pipeline**：支持"模型 A 起草 → 模型 B 评审 → 模型 A 修订"工作流
- **Claude Code / OpenCode 集成**（通过 slash 命令，可选）

总代码量约 900 行 Python，无框架，无数据库，无 Web UI。

## 快速开始

```sh
git clone https://github.com/hziq/llm-pm-bench
cd llm-pm-bench
cp .env.example .env
# 编辑 .env 填入你的 API key

# 把 config.yaml 指向你的 provider（OpenAI / LiteLLM / Ollama / vLLM / ...）
$EDITOR config.yaml

# 验证连通
python3.12 scripts/ask.py --list
python3.12 scripts/ask.py gpt-4o-mini "say hi"

# 把第一个 task 跑在所有配置的模型上
python3.12 scripts/run.py 01-jargon-explanation

# 看产出（每个模型一个文件夹）
ls runs/
```

## 目录结构

```
llm-pm-bench/
├── README.md / README_zh.md      # 入口文档（中英）
├── ARCHITECTURE.md               # 设计原理 + 多 Agent 模式
├── CONTRIBUTING.md               # 欢迎/不欢迎的贡献
├── LICENSE                       # MIT
├── config.yaml                   # endpoint + 模型 + 默认参数
├── .env.example                  # API key 模板
├── scripts/
│   ├── lib.py                    # API + env 加载 + frontmatter 解析
│   ├── ask.py                    # 单次调用器（多 Agent 编排基础）
│   ├── run.py                    # 批量跑测（多模型并发）
│   ├── cross_check.py            # 多模型并跑 + 事实差异 diff
│   ├── pipeline.py               # 声明式多步流水线
│   └── usage.py                  # LiteLLM 专用：余额查询
├── tasks/                        # 5 个示例 task 模板
│   ├── 01-jargon-explanation.md       # 短输出 + 强约束
│   ├── 02-meeting-summary.md          # 长上下文 + 结构化输出
│   ├── 03-prd-draft.md                # 指令遵循 + 长输出
│   ├── 04-design-contradiction.md     # 跨两份文档推理
│   └── 05-sql-debug.md                # 代码生成 + 领域推理
├── inputs/                       # 示例素材（mock）
├── pipelines/
│   └── draft-review-revise.yaml  # 经典三步流水线
├── reports/
│   └── _template.md              # 报告骨架
└── runs/                         # 跑测产出（git 忽略）
```

## 5 个示例 task 各测什么

| # | 任务 | 考察点 | 为什么重要 |
|---|---|---|---|
| 01 | 术语解释 | 领域知识、短输出、强约束 | 最快判断"模型懂不懂我的领域" |
| 02 | 会议纪要 | 长上下文、结构化输出 | 真实 PM/经理工作流 |
| 03 | PRD 草稿 | 指令遵循、长生成、判断力 | 测"能直接当起点" vs "套通用模板" |
| 04 | 设计矛盾识别 | 跨两份长文档推理 | 测模型能否同时把两件事放在脑里 |
| 05 | SQL 排查 | 代码生成 + 领域 + 安全规则 | 暴露模型是否会编造字段或假设结果 |

**这些是模板**。把它们适配到你的领域——把 `inputs/02-meeting/transcript.txt` 换成你自己的会议，把 `tasks/02-meeting-summary.md` 的 rubric 改成你关心的维度。

## 核心概念

### Orchestrator vs Workers
编排者（你 / ChatGPT / Claude Code / OpenCode）决定评测什么、判断结果、做最终决策。`scripts/` 里的脚本是 **workers**，只负责执行 API 调用和记录输出。这种分离是有意为之：任何 LLM CLI 工具都能当编排者，不需要框架。

### 通过架构控制幻觉
不要只靠 prompt engineering。用**跨模型验证**：同一个 prompt 同时发给 2-3 个模型，让你的编排者 diff 输出。单点幻觉会被另一个模型曝光。

```sh
python3.12 scripts/cross_check.py "总结这段文档：..."
# → runs/crosscheck-<时间戳>.md，含并排输出 +
#   自动抽取的"需要人工确认的事实线索"
```

### 隔离原则
评测产出（`runs/`）**永远不**写入你的知识库或生产数据。如果想把某个产出"晋升"到知识库，必须手动操作。这防止幻觉内容污染下游工作。

### 不要框架
没有 CrewAI、LangGraph、AutoGen。整个编排词汇表只有："跑一个脚本，读它的输出，决定下一步做什么。" 如果你的工作流复杂到 250 行脚本搞不定，那你已经超出这个仓库的范围了，应该看 LangGraph。

## 可选：Claude Code 集成

如果你用 [Claude Code](https://www.anthropic.com/claude-code) 当 CLI 编排者，可以装 slash 命令调用本仓库：

```sh
# 在 ~/.claude/commands/ 下定义示例命令：
#   /ask <model> <prompt>     → 包装 scripts/ask.py
#   /cross-check <prompt>     → 包装 scripts/cross_check.py
#   /pipeline <name>          → 包装 scripts/pipeline.py
```

详见 `ARCHITECTURE.md` 和示例命令文件。

## 可选：OpenCode 集成

[OpenCode](https://opencode.ai) 原生支持 subagent。你可以配置 subagent 使用本仓库评测过的模型。详见 `ARCHITECTURE.md` § "OpenCode integration"。

## 何时用 / 何时不用

**✅ 适合：**
- 想对比 2-5 个 LLM 在你真实任务上的表现
- 想知道自部署模型能不能替代付费 API
- 单兵开发者 / PM / 分析师，不想学框架
- 想要幻觉控制但没钱买 ground truth

**❌ 不适合：**
- 需要严谨统计评估（用 `lm-eval-harness`）
- 需要测 100+ 任务（用真正的 benchmark）
- 需要 fine-tuning、RAG、训练基础设施
- 需要给非技术 stakeholder 做 web dashboard

## Provider 兼容性

已测试：
- ✅ LiteLLM proxy（任意模型）
- ✅ OpenAI API
- ✅ 自部署 vLLM
- ✅ 自部署 Ollama（用 `endpoint: http://localhost:11434/v1` 和 `api_key: ollama`）
- ⚠️ Anthropic API 直连：需要 LiteLLM 中转（脚本用 OpenAI 兼容 payload）

`scripts/usage.py` 仅支持 LiteLLM 兼容 gateway。

## 缘起

源于在工业 APS/MES SaaS 产品上评测 3 个国内自部署模型（Kimi K2.5、GLM-5、Qwen 3.5）能否替代 Claude Opus 4.6 完成日常 PM 工作的实际需要。原始评测发现：在中文短输出 + 强约束任务上，Kimi K2.5 有时**优于** Claude——这个结论值得把方法论开源出来。

## License

[MIT](LICENSE)
