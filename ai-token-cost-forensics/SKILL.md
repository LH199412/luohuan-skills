---
name: ai-token-cost-forensics
description: Diagnose unexpected token/cost spikes in Codex-style AI agent environments. Locate the likely consumer, quantify usage from local config, model catalog, thread history and rollout logs (read-only; secrets redacted), and rank fixes across model tier, reasoning effort, context governance, retries and metering. Use when an AI token bill is suddenly high or the spend source is unknown.
---

# Luohuan · AI Token 成本取证专家

## 用途

当 AI 编码 Agent / LLM 应用的 token 账单突然暴涨、或你根本不知道钱花在哪时，用本 skill 根据本地证据定位可能的消耗源，并直接给出止血动作。它输出的是可执行的诊断和按影响排序的修复，不是通用方法论。

当前实现面向 Codex 风格的本地目录；它不会连接供应商后台，也不会自动修改配置或执行修复。

## 先记住一个结论（本 skill 最反直觉、也最值钱的一点）

「谁在烧 token」往往不是你以为的那一层。一个多模型应用的账单暴涨，真凶可能是底层编码 Agent 自身——默认用了最贵模型 + 高推理强度 + 超长上下文——而不是业务代码里的评审/重试逻辑。所以第一步永远是**定位真实消费者**，而不是急着去改业务代码。

## 何时用

- token / 费用突然异常升高，且来源不明
- 单次请求平均 token 数异常大（用「总 token ÷ 请求数」估算）
- 想给 Agent / LLM 应用建立 token 成本护栏与对账

## 何时不用

- 只想选模型、比价格（直接看供应商官方价格页）
- 纯 API 计费争议（去供应商后台核对）
- 需要直接修改配置、数据库或自动修复（本 skill 只做只读诊断）

## 五步流程

1. **定位消费者**：先问「这笔钱是哪个客户端/进程/模型花出去的」，对照本地账本与供应商后台。
2. **量化**：跑 `scripts/scan_usage.py` 扫描本地配置、会话历史、rollout 日志，得到按会话/模型的分布、单请求分布、缓存占比。
3. **找放大器**：看上下文是否逐轮重发、推理强度、模型档位、重试、多 agent 分叉、图片输入、固定工具/技能开销。
4. **止血**：按 `references/fix-playbook.md` 的优先级改（模型档位 → 推理强度 → 上下文治理 → 重试收敛 → 计量闭环）。
5. **建护栏**：补计量/账单对齐，设预算与上下文软上限，让异常再次发生时能第一时间定位。

## 输入

脚本只读取 `--codex-home` 指向的本地目录，支持以下实际输入：

- `config.toml`：模型、推理强度、模型提供方，以及 plugins / MCP 配置段数量
- `models.json`：模型目录中的 slug、上下文窗口、默认推理强度、输入模态
- `thread_history_1.sqlite`：`thread_turns` 表中的会话轮数
- `archived_sessions/*.jsonl`：包含 usage 字段的本地 rollout 日志

可用参数覆盖路径：

```bash
python3 scripts/scan_usage.py --codex-home ~/.codex
python3 scripts/scan_usage.py --codex-home /path/to/.codex --thread-db /path/to/thread_history_1.sqlite --rollout-dir /path/to/archived_sessions
```

## 输出

脚本输出纯文本诊断，包括：

- 模型配置与模型目录摘要
- 会话总轮数和轮数最多的 thread 列表（可能包含 `thread_id`）
- rollout 文件数、请求次数、输入/输出 token、缓存比例和请求规模分布
- 按影响排序的修复建议
- 扫描到的 rollout 文件名（可能包含本地会话标识）

输出可能包含 `thread_id`、会话文件名和本地路径等关联元数据。分享报告前应先检查并脱敏这些信息。

## 安全边界

- 全程只读：不上传数据、不访问网络、不写入配置或数据库、不执行自动修复。
- 不提取或输出 API key、`.env`、密码或令牌；脚本对配置值做有限脱敏，但不能替代人工复核。
- 诊断只依据本地可验证证据 + 供应商后台口径；不把估算当真实账单。
- 当前只支持 Codex 风格的配置、模型目录、thread SQLite 和 rollout JSONL，不声称支持其他 Agent、数据库或日志格式。
- 修改配置、数据库或调用真实模型前，必须获得明确授权并自行备份。

## 可执行脚本

- `scripts/scan_usage.py`：只读扫描（支持 `--codex-home`、`--thread-db`、`--rollout-dir`），输出结构化诊断 + 排名后的修复建议。

## 修复手册

- `references/fix-playbook.md`：修复杠杆（按性价比排序）、config 示例、对账与护栏模板。

## English

Luohuan AI Token Cost Forensics is a local, read-only diagnostic skill for Codex-style AI agent environments. It helps locate the likely source of unexpected token or cost growth, quantify local usage, and prioritize fixes.

Inputs: a Codex-style home containing `config.toml`, `models.json`, `thread_history_1.sqlite`, and `archived_sessions/*.jsonl`. Paths can be overridden with `--codex-home`, `--thread-db`, and `--rollout-dir`.

Outputs: a plain-text report with model configuration, thread counts, rollout token statistics, cache ratio, request-size distribution, and ranked remediation suggestions. The report may include thread IDs, session filenames, and local paths.

Safety and limits: the script does not upload data, access the network, modify configuration or databases, or apply fixes. It performs limited redaction of configuration values but does not guarantee that every sensitive string is removed; review the output before sharing. It does not replace provider billing data, and it currently supports only the Codex-style inputs listed above.
