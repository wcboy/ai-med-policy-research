# AI 医药政策研究 Skill

[English](README.md) | [中文](README.zh-CN.md)

`ai-med-policy-research` 是一个面向 Codex 的医药政策研究 Skill。它把 AI 辅助政策研究组织成可追溯、可复核、可移交的 Agent 工作流，覆盖前瞻性方法学设计、RAW 数据治理、结构化数据与数据库协议、PROSPEC 执行包、硬状态机门禁，以及基于证据的质量审查。

这个 Skill 适用于以下场景：从论文中提炼方法学，将方法学交给另一个 Agent 或多个子 Agent 执行，基于原始数据进行分析复刻，最后在不泄漏已知结论或论文身份的前提下比较产出差异。

## 解决的问题

AI Agent 可以快速生成政策研究草稿，但在严肃研究中常见的问题是：

- 跳过原始数据学习，只使用最显眼或最方便的 RAW 文件；
- 让已知论文结论反向塑造方法学或审评标准；
- 把论文标题、DOI、URL、文件名等暴露给执行 Agent，导致 Agent 搜索原论文并污染复刻；
- 没有证据引用却声称质量审查通过；
- 数据库清洗、标签、入库或查询设计已经不合适时，仍然做最小修补而不是从治理后的 raw/staging 层重建；
- 遇到超时、内存溢出或工具失败后，没有受控迭代记录，却继续声称任务完成。

本 Skill 将这些失败模式显式化，并要求 Agent 在完成前通过文件、状态机和 validator 的门禁。

## 核心能力

- 研究契约：明确政策对象、研究问题、边界、预期产出、数据范围、污染边界和最小可接受产出。
- 方法学隔离：将方法学与已知结果、清洗数据、标签、既有报告和预期结论解耦。
- 来源身份盲化：论文标题、DOI、URL、引用、作者/期刊字符串、精确文件名不得进入执行侧 artifacts。
- RAW 数据门禁：分析、清洗、入库、建模或复刻前，必须先生成 `01_inputs/raw_inventory.json` 和同步的 `01_inputs/README_DATA.md`。
- 结构化数据治理：从研究问题反向设计清洗规则、标签扩增、数据库 schema、入库、存储、查询/API 协议和重建触发条件。
- PROSPEC 执行：为每个子任务保留前瞻性预期、研究边界、操作流程、结构化数据协议、并发契约、证据链和完成门禁。
- 执行状态机：强制 `INIT -> METHOD_LOCKED -> TASKS_LOCKED -> EVIDENCE_COMPLETE -> REVIEWED -> ACCEPTED`，失败则进入 `ITERATE`。
- Validator 门禁：拒绝跳步、缺失 artifact、RAW 覆盖不完整、公开身份泄漏、失败工具调用支撑“通过”、以及无依据的 `ACCEPTED`。

## 仓库结构

```text
ai-med-policy-research/
  SKILL.md
  agents/openai.yaml
  references/artifact-protocol.md
  references/quality-checklist.md
  scripts/validate_execution_control.py
```

`SKILL.md` 是 Codex Skill 的入口文件。`references/` 定义 artifact 协议和质量审查清单。`scripts/validate_execution_control.py` 是针对生成 run folder 的硬校验器。

## 安装

将仓库克隆到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/wcboy/ai-med-policy-research.git ~/.codex/skills/ai-med-policy-research
```

在 Codex 中调用：

```text
Use $ai-med-policy-research to ...
```

## 典型流程

1. 建立研究契约。
2. 声明 artifact protocol 并创建 run folder。
3. 如果从论文提炼方法学，先完成来源身份盲化。
4. 在分析 RAW 数据前创建 `raw_inventory.json` 和 `README_DATA.md`。
5. 冻结方法学、审评预期、PROSPEC 协议和必要的数据协议。
6. 拆解子任务，并写入机器可检的 PROSPEC packets。
7. 在资源限制下执行任务，并记录 tool call。
8. 写入基于证据的质量审查矩阵。
9. 在声称 `REVIEWED`、`ACCEPTED` 或 goal 完成前运行 validator。
10. 如果任一门禁失败，回到失败层并记录迭代。

## Validator

对生成的研究 run folder 运行校验：

```bash
python3 scripts/validate_execution_control.py /path/to/run_folder
```

validator 会检查：

- `manifest.json` 与 `execution_state.json` 是否一致；
- 状态流转日志和质量门禁权限是否合法；
- restricted 来源身份扫描词和公开 artifacts 泄漏扫描；
- `raw_inventory.json` 与 `README_DATA.md` 是否覆盖一致；
- `METHOD_LOCKED` 前方法学、审评预期和 PROSPEC artifacts 是否冻结；
- 可执行子任务是否有对应的 PROSPEC packet；
- tool-call 引用是否存在，以及非成功调用是否被错误用于“通过”证据；
- `quality_review.md` 是否包含证据约束矩阵；
- `ACCEPTED` 状态是否有最小可接受产出和全部通过的质量行。

## 生成的 Run Artifacts

文件型执行的默认 run folder 结构见 `references/artifact-protocol.md`。关键文件包括：

- `00_contract/research_contract.md`
- `00_contract/source_identity_registry.md` restricted
- `00_contract/source_identity_scan_terms.json` restricted
- `01_inputs/raw_inventory.json`
- `01_inputs/README_DATA.md`
- `01_inputs/structured_data_protocol.md`
- `02_method/methodology_framework.md`
- `02_method/prospec_execution_protocol.md`
- `04_workflow/prospec_tasks.json`
- `05_trace/tool_call_log.jsonl`
- `06_review/quality_review.md`
- `08_output/minimum_acceptable_output.md`
- `09_execution_package/` public handoff package

restricted 身份文件不得传给执行 Agent，也不得放入公开 execution package。

## 适用场景

适合用于：

- 医药政策研究；
- 政策效果评价工作流；
- 文献方法学提取与盲化复刻；
- Agent/子 Agent 研究任务拆解；
- 统计分析或数据库分析前的结构化 RAW 数据治理；
- 需要可追溯证据链的论文、报告或决策支持研究。

它不是临床、法律或监管判断的替代品；它是一个研究治理和工作流控制 Skill，不是医疗建议系统。

## 开发校验

校验 Skill 包：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/ai-med-policy-research
python3 -m py_compile ~/.codex/skills/ai-med-policy-research/scripts/validate_execution_control.py
```

## 贡献说明

- `SKILL.md` 保持为核心操作说明。
- 详细可复用协议放在 `references/`。
- 确定性门禁放在 `scripts/`。
- 不要为了方便削弱盲化、RAW 数据门禁或状态机检查。
- 如果旧 run 在新 validator 下失败，应迁移旧 artifacts，而不是放松门禁。
