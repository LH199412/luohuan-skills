# Luohuan Skills

本仓库用于公开发布 Luohuan 的 Agent Skills。当前包含：

- [`luohuan-knowledge-pipeline`](./luohuan-knowledge-pipeline/) — Knowledge Pipeline（知识生产流水线）

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
