# Luohuan Skills

本仓库用于公开发布 Luohuan 的 Agent Skills。当前包含：

- [`luohuan-knowledge-pipeline`](./luohuan-knowledge-pipeline/) — Knowledge Pipeline（知识生产流水线）
- [`ai-token-cost-forensics`](./ai-token-cost-forensics/) — Luohuan AI Token Cost Forensics（AI Token 成本取证专家）

## luohuan-knowledge-pipeline

- 技术标识：`luohuan-knowledge-pipeline`
- 展示名称：Luohuan Knowledge Pipeline
- 版本：0.1.0
- 许可证：[MIT](./LICENSE)
- 形态：面向 AI Agent（Claude Code / Codex / 兼容 Agent Skills 的客户端）的 `SKILL.md` 技能

### 用途

把「来源登记 → 增量采集 → 解析/清洗/脱敏 → 指纹去重 → 入库 → 版本记录 → Skill 候选 → 校验/测试/审核 → 发布 → 运行反馈 → 更新或回滚」这一知识生产流水线固化为可复用的方法论，指导 Agent 安全、幂等、可追溯地建设知识库，并把知识沉淀为可审核、可测试的 Skill。

### 使用方式

1. 把 `luohuan-knowledge-pipeline/` 目录放到 Agent 的技能目录（例如 Claude Code 的 `~/.claude/skills/`，或 Codex 的 skills 目录）。
2. 在任务里说明要采集的知识源、范围和验收标准，Agent 会按 `SKILL.md` 的方法论执行。
3. 示例触发语：
   - 「用 luohuan-knowledge-pipeline 把 docs/ 目录增量采集进知识库，并做去重与版本记录。」
   - 「把这个知识库变更生成一个 Skill 候选，先做结构校验再交给我审核。」

### 许可证

本项目采用 [MIT License](./LICENSE)，版权 © 2026 Luohuan。

### 免责声明

本技能描述的是方法论与工程约束，不含任何密钥、令牌或私有数据；外部内容一律视为不可信输入。

## ai-token-cost-forensics

- 技术标识：`ai-token-cost-forensics`
- 展示名称：Luohuan AI Token Cost Forensics（AI Token 成本取证专家）
- 版本：0.1.0
- 许可证：[MIT](./ai-token-cost-forensics/LICENSE.md)
- 形态：面向 Codex 风格本地环境的只读 token 成本诊断 Skill

### 用途

根据本地 `config.toml`、`models.json`、thread SQLite 和 rollout JSONL 证据，辅助定位 token/费用异常的主要消耗来源，并按性价比给出模型档位、推理强度、上下文治理、重试与计量修复建议。完整介绍见 [`ai-token-cost-forensics/README.md`](./ai-token-cost-forensics/README.md)。

### 使用方式

把 `ai-token-cost-forensics/` 放入 Agent 的 skills 目录，或显式调用 `$ai-token-cost-forensics`。在技能目录内运行：

```bash
python3 scripts/scan_usage.py --codex-home ~/.codex
```

脚本只做本地只读诊断，不上传数据、不修改配置或数据库；详细参数、输出与限制见技能目录中的 README。
