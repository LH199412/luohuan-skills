# Luohuan · AI Token 成本取证专家

**Luohuan AI Token Cost Forensics** · 候选版本 0.1.0（未正式发布）

一个面向 Codex 风格本地环境的只读 token 成本诊断工具：当 AI Agent / LLM 应用的 token 账单暴涨时，帮助定位可能的消耗源并给出可执行的止血建议。

## 解决什么问题

- 账单突然涨了几倍到几十倍，但不知道钱花在哪
- 分不清是模型选型、上下文膨胀、推理强度过高、重试放大，还是计量缺失
- 改了业务代码却不见下降——真正的消费者可能在别处

## 适用环境与输入

当前实现只读取 `--codex-home` 指向的本地目录：

- `config.toml`：模型、推理强度、模型提供方、plugins/MCP 配置段
- `models.json`：模型目录与上下文窗口
- `thread_history_1.sqlite`：会话轮数
- `archived_sessions/*.jsonl`：本地 rollout usage 记录

可用 `--thread-db` 和 `--rollout-dir` 覆盖后两者路径。它不连接供应商后台，也不支持其他 Agent、数据库或日志格式。

## 使用方式

1. 把本 skill 放进 skills 目录，或显式调用 `$ai-token-cost-forensics`。
2. 运行：

   ```bash
   python3 scripts/scan_usage.py --codex-home ~/.codex
   ```

3. 查看纯文本报告中的模型配置、thread 轮数、token 分布、缓存比例和修复建议。
4. 按 `references/fix-playbook.md` 的顺序评估修复；脚本本身不会修改任何配置。

自定义路径示例：

```bash
python3 scripts/scan_usage.py \
  --codex-home /path/to/.codex \
  --thread-db /path/to/thread_history_1.sqlite \
  --rollout-dir /path/to/archived_sessions
```

## 输出

- 模型配置与模型目录摘要
- 会话总轮数和轮数最多的 thread 列表
- rollout 文件数、请求次数、输入/输出 token、缓存比例
- 单请求 token 规模分布和会话累计峰值
- 按影响排序的修复建议

报告可能包含 `thread_id`、会话文件名和本地路径。分享前请人工检查并脱敏。

## 隐私与安全

- 本地只读：不上传数据、不访问网络、不写入配置或数据库、不自动修复
- 不提取或输出 API key、`.env`、密码或令牌；脱敏是有限且尽力而为的，不能替代人工复核
- 只依据本地可验证证据和供应商后台口径；估算值不等于真实账单
- 修改配置、数据库或调用真实模型前，必须获得明确授权并备份

## 限制

- 目前只支持 Codex 风格输入；其他 Agent、任意数据库或其他日志格式不在当前实现范围
- rollout 统计依赖日志中可识别的 usage 字段，不能替代供应商账单
- 输出是诊断建议，不是自动修复；不会替用户改模型、预算或配置

## English

Luohuan AI Token Cost Forensics is a local, read-only diagnostic skill for Codex-style AI agent environments. It locates likely token/cost spikes, quantifies usage from local configuration and logs, and ranks remediation options.

It reads `config.toml`, `models.json`, `thread_history_1.sqlite`, and `archived_sessions/*.jsonl` under `--codex-home`; `--thread-db` and `--rollout-dir` override the latter two paths. It prints model configuration, thread counts, request-size statistics, cache ratio, and ranked suggestions. Reports may contain thread IDs, session filenames, and local paths.

It does not upload data, access the network, modify configuration or databases, or apply fixes. Redaction is limited and does not replace manual review. It does not replace provider billing data and currently supports only the Codex-style inputs listed above.

## 版本记录

- `0.1.0` — 初始公开发布候选；尚未正式发布或通过平台审核。

## License

MIT。许可证全文见 `LICENSE.md`；本候选版本未修改版权行。
