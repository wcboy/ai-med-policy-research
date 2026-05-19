---
name: ai-med-policy-research
description: Decompose and run AI-assisted medical or pharmaceutical policy research as a traceable, reproducible Agent workflow with research-goal definition, RAW data snapshot governance, structured-data/database governance, PROSPEC methodology execution protocols, execution-state control, knowledge organization, tool-interface planning, file/artifact generation protocols, evidence-bound quality review, and self-feedback iteration. Use when Codex is asked to design or execute 医药政策研究, 政策文本分析, 政策落地问题研究, AI辅助政策研究方法学, /goal-style research workflows, research task decomposition, RAW data README_DATA.md snapshots, structured data cleaning/入库/调用 protocols, methodology framework files, quality-review checklists, validator-gated execution, or iterative Agent research pipelines.
---

# AI 辅助医药政策研究

## Overview

Use this skill to turn a medical policy research request into a controlled Agent research loop. Treat AI as a traceable research operator, not a one-shot answer generator: define the policy object and question first, prepare governed data and knowledge structure, run a reproducible workflow, review output quality, and iterate until a minimum acceptable research deliverable exists.

## Method Core

Preserve these principles in every task:

- Start from the policy research object and question, not from model output.
- Make the research process decomposable: every subtask should have an input, method, output, and review criterion.
- Govern research data before using it for claims: source, version, scope, reliability, and gaps must be explicit.
- Before a later Agent applies a methodology framework to raw inputs, it must first learn and identify all available RAW data by creating `01_inputs/raw_inventory.json` and `01_inputs/README_DATA.md`: a machine-readable inventory plus complete information snapshot covering every raw file/table/sheet/source. Analysis, cleaning, ingestion, modeling, or replication must not start from raw data until both are synchronized and the snapshot is frozen.
- For structured data, reverse-design the cleaning, label expansion, database schema, ingestion, storage, and invocation protocol from the research question and expected analytical output before analysis begins.
- Treat structured-data databases as rebuildable research infrastructure. If later calls reveal that cleaning, labeling, ingestion, schema, storage, or query design should improve, rebuild and reload the database from governed raw/staging sources with a new versioned protocol instead of making a minimum viable recovery patch, unless the user explicitly requests an emergency hotfix.
- Organize knowledge visually or structurally when relationships matter: policies, tools, stakeholders, problems, evidence, and solutions should be linkable.
- Use standard tool interfaces for retrieval, databases, graph tools, statistics, visualization, document generation, and review.
- When generating files, use an explicit artifact protocol for file names, storage location, manifest records, call order, and version/freeze status.
- Keep Agent calls traceable: record what data and tools were used, what intermediate result was produced, and which uncertainty remains.
- When extracting or generalizing methodology, decouple the methodology from known results, cleaned datasets, labeled answers, prior reports, and expected conclusions. Treat these materials as held-out validation artifacts unless the user explicitly designates them as training or calibration data.
- When extracting methodology from a paper for later blind execution, also decouple source identity. Paper title, authors, journal, DOI, URL, citation string, and exact PDF filename are identity leaks because they let a later Agent locate the real paper online and import its conclusions. Put identity mapping and scan terms only in restricted parent/reviewer artifacts; public methodology artifacts and `manifest.json` should use blinded IDs such as `paper:P001` and must not expose real forbidden terms.
- For data review, define review expectations prospectively under unknown paper/data results. Review expectations are positive expectations for possible research results and danger-boundary judgments for data processing; they must not be reverse-engineered from known paper conclusions or cleaned-data outcomes.
- When decomposing methodology for later Agents or subagents, preserve a PROSPEC execution packet for every subtask so the decomposed work still follows the same prospective, source-governed, traceable, quality-gated process.
- For file-backed execution, use an Execution Control Protocol: `execution_state.json` records the current state, required artifacts, subtask evidence, quality-gate permission, and transition log. An Agent must not claim quality pass, accepted output, or `/goal 完成` unless the state transition path, quality permissions, evidence references, and validator pass.
- Execution control must include resource governance for large structured data: per-subtask runtime budget, memory budget, large-file read policy, and automatic `ITERATE` on timeout, memory overflow, or resource exhaustion.
- Use quality review as the gate. If output does not match expectations, return to the right upstream step and iterate.
- Stop at a minimum acceptable output only after the quality checklist passes.

## Methodology Extraction Isolation

When the task is to refine a method, prompt, workflow, evaluation rubric, or Agent procedure, protect future independent verification from contamination:

- Declare the separation between method-building inputs, execution data, and validation data before using any known result.
- Do not derive categories, rules, scoring criteria, prompts, or acceptance thresholds from already-cleaned data, final answers, benchmark labels, polished reports, or previous Agent conclusions unless the user explicitly asks for supervised calibration.
- If known results or cleaned data have already been viewed, state that exposure and avoid claiming a fully independent validation on the same materials.
- Build the method from the research question, raw policy material classes, domain logic, tool affordances, and quality criteria first; use held-out results only after the method is fixed.
- For independent Agent verification, preserve an evidence boundary: the verifier should receive the frozen method, raw inputs, and quality checklist, not hidden expected answers.

For data review expectations specifically:

- Freeze initial review expectations before inspecting paper conclusions, cleaned-data outputs, benchmark answers, or known result summaries.
- Express each expectation as a prospective judgment: expected positive signal, plausible acceptable range, warning threshold, dangerous processing boundary, or evidence sufficiency condition.
- Do not score the method by making the expectation fit an already-known result. If an expectation was added after result exposure, mark it as a human-added or post-exposure expectation and do not use it as proof of independent predictive validity.
- Support manual additions: the user or reviewer may add review expectations at any time, but each added expectation must record author/source, time, reason, and whether known results had already been seen.

For literature methodology extraction specifically:

- Treat source identity metadata as held-out unless the user explicitly asks for citation management rather than blind replication.
- Do not put paper title, authors, DOI, journal, URL, citation string, exact PDF filename, or searchable title fragments in `methodology_framework.md`, `prospec_execution_protocol.md`, `review_expectations.md`, `task_decomposition.md`, `subagent_dispatch_plan.md`, or prompts given to execution Agents.
- Use blinded source IDs (`paper:P001`, `source:S001`) in public artifacts. Store the real mapping only in a restricted parent/reviewer artifact such as `00_contract/source_identity_registry.md`.
- Store exact identity scan terms only in restricted `00_contract/source_identity_scan_terms.json`; never place them in `manifest.json`, execution prompts, dispatch plans, or public execution packages.
- Execution Agents must not web-search the paper, infer the hidden citation, or use bibliographic lookup to recover the original article. External search is allowed only for general domain concepts or tool documentation, not for locating the source paper.
- If a title, DOI, URL, or exact filename was already exposed to an execution Agent, record the exposure and do not claim blind independent replication.

## PROSPEC Method Execution Protocol

Use PROSPEC as the required execution packet for methodology frameworks that may be handed to another Agent or split across subagents. Treat PROSPEC as "prospective specification": the method is fixed before results are inspected, and each subtask can be executed independently without hidden expectations.

Every full methodology framework and every delegated subtask should include:

- P - Prospective expectations: pre-result review expectations, danger boundaries, and evidence sufficiency conditions.
- R - Research boundary: research question, included/excluded materials, time/geography/policy scope, and held-out known results.
- O - Operating procedure: ordered steps, tool interfaces, input/output contract, and acceptance check.
- S - Structured data protocol: source inventory, cleaning rules, label expansion rules, schema, ingestion/storage plan, query or API contract, and rebuild trigger.
- P - Parallel execution contract: subtask ownership, dependencies, read/write scope, allowed shared artifacts, merge order, and conflict rule.
- E - Evidence trace: citations, file paths, database versions, tool-call logs, intermediate outputs, and unresolved uncertainty.
- C - Completion gate: quality checklist status, execution-state unlock, validator result, failed-layer return point, iteration record, and minimum acceptable output.

For subagent delegation, the parent Agent should pass only the frozen PROSPEC packet, relevant raw or governed inputs, and required interfaces. Do not pass hidden expected answers or held-out validation results to execution subagents. Validation subagents may receive observed results only after the method and prospective expectations are frozen.

## Workflow

### 1. Build the Research Contract

Before analysis, write a compact research contract:

- Research object: policy, disease area, drug/device category, payer rule, procurement mechanism, region, or institution.
- Research question: the exact problem to answer.
- Boundary: time range, geography, policy level, included/excluded materials.
- Expected output: memo, evidence table, policy map, issue list, graph, thesis section, report, or action plan.
- Research data: known files, URLs, databases, screenshots, interview notes, logs, or missing data to request.
- Structured-data contract: required analytical grain, identifiers, variables, labels, derived fields, database schema, ingestion/storage protocol, query/API contract, and rebuild rules derived from the research question.
- Contamination boundary: which known results, cleaned datasets, labels, polished reports, or prior conclusions must be withheld from methodology extraction and reserved for validation.
- Source identity boundary: for paper-derived methodology, which title/authors/DOI/journal/URL/file-name terms must be hidden from execution Agents and stored only in a restricted provenance registry.
- Prospective review expectations: initial data-review expectations and danger boundaries written before known results are inspected, plus a place for human-added expectations with source and exposure status.
- PROSPEC execution scope: which subtasks can be parallelized, what each Agent may read/write, and which outputs must be merged only after quality review.
- Quality checklist: criteria that determine whether the output is acceptable.
- Minimum acceptable output: the smallest deliverable that can be reviewed, reused, or expanded.

If the environment supports explicit goal tooling and the user asks for it, map this contract to `/goal 开始 -> 研究目标 -> 研究数据 -> 质量审查清单 -> /goal 完成`. Otherwise, keep the same structure as a written contract. Do not create or complete a tool-backed goal unless the user explicitly requested goal-mode operation.

### 1.5. Declare the Artifact Protocol

When the task asks to generate, store, update, or reuse a methodology framework as files, use `references/artifact-protocol.md`.

At minimum, declare:

- Output root: user-specified path, existing project governance path, or `./ai_policy_research_runs` when file output is requested and no path is given.
- Run folder: timestamped and slugged, so independent runs do not overwrite each other.
- Manifest: a machine-readable index of artifacts, status, source scope, contamination boundary, and validation state.
- Frozen method file: the version of the methodology used for independent verification.
- Source identity registry: restricted parent/reviewer-only mapping from blinded source IDs to paper titles, authors, DOI, URL, exact filename, and citation details. Do not include this registry in execution Agent call order.
- Source identity scan terms: restricted parent/reviewer-only exact terms used for leakage scanning. Do not include these terms in public manifest fields or execution packages.
- RAW data inventory and snapshot files: `01_inputs/raw_inventory.json` and `01_inputs/README_DATA.md`, covering all available raw files, tables, sheets, database sources, or folders before analysis starts.
- Review expectations file: pre-result expectations and human-added expectations with exposure status.
- Structured-data protocol file: database cleaning, label expansion, schema, ingestion, storage, query, and rebuild rules.
- PROSPEC execution protocol file: subtask packets, parallelization constraints, evidence trace rules, and completion gates.
- Execution-state file: machine-checkable state, allowed transitions, required artifacts, subtask output refs, tool-log refs, and quality-gate permissions.
- Call protocol: the read order an Agent must follow before executing or reviewing the workflow.

Do not write files when the user only asks for an explanation. Do not modify thesis chapters, source datasets, or cleaned validation artifacts unless the user explicitly requests that target path.

### 1.6. Apply Execution Control

When a methodology framework is handed to another Agent or executed from stored artifacts, use `references/artifact-protocol.md` and `scripts/validate_execution_control.py` as the hard gate.

Minimum state flow:

```text
INIT -> METHOD_LOCKED -> TASKS_LOCKED -> EVIDENCE_COMPLETE -> REVIEWED -> ACCEPTED
                                                          \-> ITERATE
```

Rules:

- `manifest.json` indexes artifacts; `execution_state.json` controls whether the workflow may advance.
- Each state transition must write or update the required artifacts before advancing.
- `transition_log` must show a valid state path; `REVIEWED` requires `quality_gate.review_allowed=true`, and `ACCEPTED` requires `quality_gate.accept_allowed=true`.
- If source-identity blinding is required, execution-facing artifacts must contain only blinded source IDs and must not include paper title, DOI, URL, journal, author string, citation string, exact filename, or other searchable identity terms. Public manifest fields must not include the forbidden terms used for leakage scanning.
- If raw data is available or bound for execution, `01_inputs/raw_inventory.json` and `01_inputs/README_DATA.md` are required pre-analysis artifacts. Do not enter data cleaning, ingestion, model fitting, statistical analysis, replication, or synthesis until the inventory and snapshot are synchronized and the snapshot is frozen.
- Each execution subtask must declare resource limits before dispatch: maximum runtime, maximum memory or memory class, large-file read policy, and overflow behavior.
- `tool_call_log.jsonl` entries must include stable `call_id` values so quality review can cite tool evidence.
- `quality_review.md` must contain an evidence-bound review matrix. A `通过` decision is invalid unless it cites evidence, tool logs, artifact refs, or database refs, and it must not rely on failed, timed-out, partial, skipped, or resource-exhausted tool calls.
- Run `python3 scripts/validate_execution_control.py <run_folder>` before claiming `REVIEWED`, `ACCEPTED`, a passed quality gate, or `/goal 完成`.
- If validation fails, times out, or hits memory/resource exhaustion, enter `ITERATE` or return to the failed upstream layer. Do not patch the final prose to hide the control failure.

### 2. Decompose the Research Flow

Break the policy research task into ordered units. Prefer units like:

- Collect and normalize policy materials.
- Extract policy instruments, regulatory objects, stakeholders, obligations, incentives, constraints, and timelines.
- Identify implementation problems and affected actors.
- Link problems to evidence, causes, policy tools, and possible solutions.
- Compare across regions, policies, time periods, or categories when relevant.
- Synthesize findings into the requested artifact.
- Review quality and revise.

For each unit, state the input, method, output, acceptance check, PROSPEC packet, execution-state requirements, `README_DATA.md` dependency, resource limits, and whether it can be parallelized. A subtask is parallelizable only when its read inputs, write outputs, held-out-result boundary, database access mode, large-file policy, tool-log requirement, evidence refs, and merge contract are explicit.

### 3. Govern Research Data

Before using data in conclusions:

- Record source, date, author/publisher, file path or URL, and extraction method.
- Before applying a methodology to raw data, create `01_inputs/raw_inventory.json` and `01_inputs/README_DATA.md` as the RAW data learning layer. The inventory must list every detected raw input with a stable `raw_id`; the README must cover every inventory entry, including data type, size, encoding or parser, sheets/tables, column names, units, time/geography/entity coverage, candidate keys, obvious missingness or abnormal values, potential labels, relationships across files, inspection method, coverage status, and unresolved read/parse risks.
- `README_DATA.md` is a gate, not decoration. If any available RAW input is missing from the snapshot, marked uninspected, or only vaguely summarized, the Agent must enter `ITERATE` and fix the data-learning layer before cleaning, ingestion, modeling, or replication.
- Build the snapshot with bounded inspection: metadata, headers, schemas, sheet names, sampled rows, projected columns, chunked scans, or database introspection. Do not fully load large files merely to write the README.
- Distinguish primary policy text, official data, secondary literature, user-provided artifacts, and model inference.
- Separate raw inputs, cleaned/annotated data, known final results, and validation artifacts. Do not let validation artifacts shape the method unless the task is explicitly supervised calibration.
- Keep data-review expectations separate from data-review results. Expectations are prospective; results are observed later and judged against frozen or explicitly human-added expectations.
- For structured data, derive the database design backwards from the research need: analytical grain, entity keys, time/geography/unit fields, linkage keys, controlled vocabularies, label taxonomy, derived variables, validation rules, indexes/views, and expected output schema.
- Decide whether label expansion is required before ingestion. If labels are expanded by rules, models, or humans, record label source, confidence, reviewer, timestamp, and whether known results were visible.
- Use a staged database lifecycle: immutable raw inputs -> staging/normalized tables -> canonical analysis tables -> derived views/features -> documented query/API outputs. Preserve raw data and rebuild canonical stores from governed stages rather than editing canonical outputs in place.
- Record schema version, ETL/cleaning version, source snapshot, database path or service, ingestion command, validation checks, and query contract in the artifact manifest.
- During later calls, if data cleaning, label design, ingestion, schema, storage, or query interfaces prove insufficient, immediately revise the protocol and rebuild/reload the database as a new version. Do not apply ad hoc minimum recovery fixes to preserve a flawed database except under explicit emergency instruction.
- For large structured files, forbid unbounded full reads by default. Use metadata/header inspection, bounded sampling, projection, chunked streaming, or database-backed ingestion with explicit memory/runtime limits. If a process pauses or fails due to memory overflow, record `resource_exhausted` and move to `ITERATE`.
- Mark unsupported or unverifiable claims explicitly instead of smoothing them into prose.
- Preserve original wording for policy clauses when precision matters, but summarize rather than over-quote.
- Keep version-sensitive facts tied to concrete dates.

### 4. Organize Knowledge

Build a structured representation before writing final conclusions when the research contains multiple relationships:

- Nodes: policy documents, policy tools, institutions, stakeholders, implementation issues, evidence items, solutions, and outputs.
- Edges: regulates, funds, constrains, incentivizes, conflicts with, causes, mitigates, supports, contradicts, or requires.
- Views: tables for evidence, diagrams for workflows, graphs for relationship-heavy topics, timelines for policy evolution.

The goal is not decoration. Use visualization or graph structure only when it improves traceability, comparison, or explanation.

### 5. Plan Standard Tool Interfaces

List the tools or interfaces needed before running the workflow:

- Retrieval/search for policy documents and literature.
- File parsers for PDF, DOCX, XLSX, CSV, JSON, HTML, or screenshots.
- Data stores or query engines for structured evidence.
- Database build/rebuild tooling for structured data: schema validation, ETL, label expansion, ingestion, versioned storage, query/API tests, and rebuild manifest.
- Graph or visualization tools for knowledge organization.
- Statistical or comparison tools for quantitative analysis.
- Document generation tools for reports, thesis text, memos, or exports.
- Artifact storage and manifest tools for generated methodology files, review expectations, trace logs, and iteration records.

Prefer existing project tools and local data pipelines over inventing a new one.

### 6. Run a Traceable Agent Workflow

Execute the work as a logged loop:

1. State the current subtask and expected output.
2. Load the subtask's PROSPEC packet and confirm the held-out-result boundary.
3. Confirm whether source-identity blinding applies; if yes, do not use paper-title, DOI, URL, citation, or filename lookup.
4. Read or retrieve the minimum evidence needed.
5. Call tools with clear purpose.
6. Write tool calls to `tool_call_log.jsonl` with `call_id`, subtask ID, input refs, output refs, and status.
7. Separate evidence, interpretation, and recommendation.
8. Produce a reviewable artifact and update `execution_state.json` with output refs, tool-log refs, and unresolved gaps.

Avoid hidden leaps. If a conclusion depends on missing evidence, write the gap as a gap.

### 7. Review Quality

Use `references/quality-checklist.md` when the user asks for a formal review or when the output will guide a thesis, report, policy decision, or downstream workflow.

At minimum, check:

- The output answers the research question.
- PROSPEC packets exist for decomposed methodology and delegated subtasks.
- Structured-data outputs can be traced to schema, cleaning, label, ingestion, storage, and query protocols.
- Each `通过` row in the quality review cites evidence refs, tool-log refs, artifact refs, or database refs.
- `scripts/validate_execution_control.py <run_folder>` passes before the Agent claims the review passed or the run is accepted.
- Claims are traceable to data or marked as inference.
- Important policy actors, tools, implementation problems, and solutions are not silently omitted.
- The workflow can be repeated from the recorded inputs.
- The output format matches the user's requested artifact.

### 8. Iterate with Self-Feedback

If quality is not acceptable, do not merely polish the prose. Identify the failed layer and return there:

- Research question unclear -> revise the research contract.
- Data missing or unreliable -> collect, clean, or mark gaps.
- Structured data protocol insufficient -> revise cleaning/schema/label/ingestion/query protocol and rebuild/reload the database version from raw or staging sources.
- Knowledge structure incomplete -> update entities, relations, timeline, or evidence table.
- Tool call insufficient -> rerun with a better interface or query.
- Conclusion unsupported -> add evidence, downgrade the claim, or remove it.
- Execution control failed -> update the missing artifact, evidence refs, tool log, state file, or review matrix before advancing.
- Resource exhausted or memory overflow -> record the failure context, add/adjust resource limits and large-file policy, then return to `TASKS_LOCKED` before redispatch.
- Output format wrong -> regenerate from the accepted intermediate findings.

Use this iteration record:

```text
Iteration:
- Quality gap:
- Failed layer:
- Return point:
- Corrective action:
- New evidence or change:
- Pass/fail after review:
```

## Output Pattern

For substantial research tasks, produce these sections unless the user requests another format:

```text
研究目标
研究数据
RAW数据快照
结构化数据协议
流程拆解
PROSPEC执行协议
执行状态控制
工具与知识组织
阶段性发现
质量审查
自反馈迭代
最小可接受产出
待补证据或下一步
```

## Guardrails

- Do not treat AI-generated text as evidence.
- Do not let a later Agent analyze, clean, ingest, model, or replicate from raw inputs before it has generated `01_inputs/raw_inventory.json` and frozen a synchronized `01_inputs/README_DATA.md` covering all available RAW data.
- Do not let known answers, cleaned datasets, or expected conclusions contaminate methodology extraction for later independent Agent verification.
- Do not leak paper identity metadata into blind methodology packages or public manifest fields. A later Agent must not be able to identify the paper through title, DOI, URL, author/journal string, citation string, exact filename, or scan-term fields.
- Do not derive data-review expectations from known paper/data results. If humans add expectations after exposure, label them as added expectations rather than independent pre-result expectations.
- Do not use ad hoc database repair as the default response to flawed structured-data cleaning, labeling, ingestion, storage, or query design; rebuild/reload from governed sources with a revised versioned protocol.
- Do not hand decomposed methodology to another Agent without a PROSPEC packet, subtask ownership, data boundary, evidence trace rule, and completion gate.
- Do not claim `质量审查通过`, `ACCEPTED`, or `/goal 完成` for file-backed execution unless `execution_state.json`, evidence-bound `quality_review.md`, and `validate_execution_control.py` support that claim.
- Do not create unindexed methodology files. Every stored framework, expectation list, quality review, trace log, and final output should be discoverable from the run manifest.
- Do not skip quality review when the task asks for research, thesis, policy judgment, or report writing.
- Do not overclaim policy effects without local data, official statistics, or clearly cited literature.
- Do not collapse "problem", "cause", "policy tool", and "solution" into one vague paragraph when the task needs structured policy analysis.
- Do not finish with only a plan if the user asked for execution and the required evidence is available.
