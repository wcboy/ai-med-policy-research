# AI Med Policy Research Skill

[English](README.md) | [中文](README.zh-CN.md)

`ai-med-policy-research` is a Codex skill for AI-assisted medical and pharmaceutical policy research. It turns policy research work into a traceable Agent workflow with prospective methodology design, RAW data governance, structured-data/database protocols, PROSPEC execution packets, hard state-machine gates, and evidence-bound quality review.

The skill is designed for research workflows where an Agent may extract a methodology from literature, hand it to another Agent or subagents, run analysis against raw data, and then compare outputs without leaking known conclusions or paper identity into execution.

## What It Solves

AI Agents can produce useful policy research drafts, but they often fail in ways that are hard to audit:

- skipping data discovery and using only convenient raw files;
- letting known paper conclusions shape the method or review standard;
- exposing paper titles, DOI, URLs, or filenames to an execution Agent, causing it to search for the original paper;
- claiming quality review passed without evidence;
- patching flawed databases instead of rebuilding from governed raw/staging sources;
- stopping after a crash, timeout, or memory overflow without a controlled iteration record.

This skill makes those failure modes explicit and blocks completion until the required artifacts and validator checks support the claim.

## Core Capabilities

- Research contract: define policy object, question, boundary, expected output, data scope, contamination boundary, and minimum acceptable output.
- Methodology isolation: keep methods separate from known results, cleaned data, labels, prior reports, and expected conclusions.
- Source-identity blinding: keep paper title, DOI, URL, citation, author/journal strings, and exact filename out of execution-facing artifacts.
- RAW data gate: require `01_inputs/raw_inventory.json` and a synchronized `01_inputs/README_DATA.md` before analysis, cleaning, ingestion, modeling, or replication.
- Structured-data governance: reverse-design cleaning, labels, schema, ingestion, storage, query/API contract, and rebuild triggers from the research question.
- PROSPEC execution: preserve prospective expectations, research boundary, operating procedure, structured-data protocol, parallelization contract, evidence trace, and completion gate for every subtask.
- Execution state machine: enforce `INIT -> METHOD_LOCKED -> TASKS_LOCKED -> EVIDENCE_COMPLETE -> REVIEWED -> ACCEPTED`, with `ITERATE` for failed gates.
- Validator-gated completion: reject skipped transitions, missing artifacts, incomplete RAW coverage, public identity leaks, failed tool calls used as pass evidence, and unsupported `ACCEPTED` claims.

## Repository Layout

```text
ai-med-policy-research/
  SKILL.md
  agents/openai.yaml
  references/artifact-protocol.md
  references/quality-checklist.md
  scripts/validate_execution_control.py
```

`SKILL.md` is the Codex skill entrypoint. The reference files define the artifact protocol and review checklist. The validator is the hard gate used against generated run folders.

## Installation

Clone this repository into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/wcboy/ai-med-policy-research.git ~/.codex/skills/ai-med-policy-research
```

Then invoke it in Codex with:

```text
Use $ai-med-policy-research to ...
```

## Typical Workflow

1. Build a research contract.
2. Declare the artifact protocol and create a run folder.
3. If extracting methodology from a paper, blind source identity before handoff.
4. Create `raw_inventory.json` and `README_DATA.md` before touching raw data analytically.
5. Freeze methodology, review expectations, PROSPEC protocol, and required data protocols.
6. Decompose subtasks and write machine-readable PROSPEC packets.
7. Execute with logged tool calls and resource limits.
8. Write an evidence-bound quality review.
9. Run the validator before claiming `REVIEWED`, `ACCEPTED`, or goal completion.
10. If any gate fails, return to the failed layer and record the iteration.

## Validator

Run the validator against a generated research run folder:

```bash
python3 scripts/validate_execution_control.py /path/to/run_folder
```

The validator checks:

- `manifest.json` and `execution_state.json` consistency;
- valid transition log and quality gate permissions;
- restricted source-identity scan terms and public leakage scan;
- `raw_inventory.json` to `README_DATA.md` coverage;
- frozen method/review/PROSPEC artifacts before `METHOD_LOCKED`;
- required PROSPEC packets for executable subtasks;
- valid tool-call references and non-success calls not being used as pass evidence;
- evidence-bound `quality_review.md`;
- final `ACCEPTED` output requirements.

## Generated Run Artifacts

For file-backed execution, the default run folder shape is documented in `references/artifact-protocol.md`. Important files include:

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

Restricted identity files should not be passed to execution Agents or included in public execution packages.

## When To Use

Use this skill for:

- medical or pharmaceutical policy research;
- policy effect evaluation workflows;
- literature-methodology extraction and blind replication;
- Agent/subagent task decomposition for research pipelines;
- structured RAW data governance before statistical or database-backed analysis;
- thesis, report, or decision-support work that needs reproducible evidence trails.

Do not use it as a substitute for clinical, legal, or regulatory judgment. It is a workflow-control and research-governance skill, not a medical advice system.

## Development Checks

Validate the skill package:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/ai-med-policy-research
python3 -m py_compile ~/.codex/skills/ai-med-policy-research/scripts/validate_execution_control.py
```

## Notes For Contributors

- Keep `SKILL.md` focused on operational instructions.
- Put detailed reusable protocols in `references/`.
- Put deterministic gates in `scripts/`.
- Do not weaken blinding or state-machine checks for convenience.
- If a failed legacy run becomes invalid under the validator, migrate the run artifacts instead of relaxing the gate.
