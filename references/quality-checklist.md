# Quality Checklist

Use this checklist to review AI-assisted medical and pharmaceutical policy research outputs. Mark each item as `通过`, `需迭代`, or `无法独立验证`.

## Research Contract

- The policy object and research question are explicit.
- Scope boundaries are concrete: time, region, policy level, data sources, and exclusions.
- The expected output and minimum acceptable output are defined.
- The review criteria are known before final writing.

## Data Governance

- Every material claim is tied to a source, file path, URL, data table, or marked inference.
- Primary policy texts are distinguished from secondary interpretation.
- Version-sensitive facts include concrete dates.
- Missing or weak evidence is marked as a gap, not hidden in confident prose.
- Data cleaning, filtering, or extraction choices are reproducible.

## Structured Data and Database Governance

- Structured data design is reverse-derived from the research question, expected claims, analytical grain, and output schema before analysis starts.
- Cleaning rules, entity keys, time/geography/unit normalization, missingness rules, exclusion rules, and validation checks are documented.
- Label expansion needs are decided prospectively; every added label records source, rule/model/human reviewer, confidence, timestamp, and result-exposure status.
- Database layers are explicit: immutable raw inputs, staging/normalized tables, canonical analysis tables, derived views/features, and query/API outputs.
- Schema version, ETL/cleaning version, label version, database path or service, ingestion command, validation result, and freeze status are recorded.
- Query or API calls use the documented invocation contract and return traceable provenance columns or references.
- If later execution shows cleaning, label design, ingestion, storage, schema, or query design should change, the database is rebuilt/reloaded from raw or staging sources as a new version instead of being minimally patched in place, unless the user explicitly requested an emergency hotfix.

## Methodology Isolation

- Method-building inputs, execution data, and validation data are explicitly separated.
- Known results, cleaned datasets, labels, benchmark answers, polished reports, or previous Agent conclusions were not used to derive the method unless the task explicitly allowed supervised calibration.
- If the Agent was exposed to known results before freezing the method, the exposure is disclosed and independent validation on those same materials is not overclaimed.
- The independent verifier receives the frozen method, raw inputs, and quality checklist, not hidden expected answers.
- Held-out or already-cleaned artifacts are used only after the method is fixed, and only for review, comparison, or validation.

## Data Review Expectations

- Data-review expectations were defined before inspecting paper conclusions, cleaned-data outputs, benchmark answers, or known result summaries.
- Each expectation is prospective: expected positive signal, acceptable range, warning threshold, dangerous processing boundary, or evidence sufficiency condition.
- Review expectations are separate from observed review results; results are judged against the frozen expectations, not used to retroactively create them.
- Human-added expectations are supported and recorded with author/source, time, reason, and exposure status.
- Post-exposure expectations are labeled clearly and are not used as evidence of independent predictive validity.

## PROSPEC Execution

- The full method and each decomposed subtask have a PROSPEC packet: prospective expectations, research boundary, operating procedure, structured data protocol, parallel execution contract, evidence trace, and completion gate.
- Subtasks marked parallelizable have explicit dependencies, read/write scopes, database access mode, forbidden held-out results, output contracts, merge rules, and parent-agent review gates.
- Execution Agents or subagents receive the frozen method, PROSPEC packet, governed inputs, and quality checklist, not hidden expected answers.
- Validation Agents inspect observed results only after the method and prospective expectations are frozen.
- The parent Agent merges subtask outputs only after required subtask quality gates pass or after failed gates are explicitly recorded as gaps.

## Research Flow

- The task is decomposed into clear subtasks with inputs, methods, outputs, and checks.
- The workflow order is defensible for policy research: define, collect, govern, extract, organize, analyze, synthesize, review.
- Intermediate artifacts can be inspected without rerunning the whole task.
- The final output can be regenerated from the recorded inputs and steps.

## Knowledge Organization

- Policy tools, implementation actors, affected groups, problems, evidence, and solutions are represented distinctly.
- Relationships are explicit when they matter: cause, constraint, incentive, responsibility, support, contradiction, or mitigation.
- Tables, graphs, timelines, or diagrams are used only when they clarify the research logic.
- Important internal relationships are not omitted when discussing a selected issue.

## Tool Use and Traceability

- Tool calls have a stated purpose.
- The output records which files, APIs, databases, or local services were used.
- Each tool call or database/file-parser access that supports a review decision has a stable `call_id` in `tool_call_log.jsonl`.
- Failed tool calls, timeouts, or non-JSON responses are recorded instead of silently substituted.
- The Agent does not fabricate unavailable data or pretend to have verified unreachable sources.

## Evidence-Bound Quality Review

`quality_review.md` must contain this review matrix before any Agent claims `质量审查通过`:

```text
| criterion_id | status | evidence_refs | tool_log_refs | artifact_refs | db_refs | decision_reason |
|---|---|---|---|---|---|---|
```

- `status` must be `通过`, `需迭代`, or `无法独立验证`.
- A `通过` row must cite at least one evidence ref, tool-log ref, artifact ref, or database ref.
- Any row that checks retrieval, file parsing, database access, statistical analysis, graph generation, or document generation must cite a `tool_log_refs` value such as `call:TC0001`.
- Any structured-data review row must cite `01_inputs/structured_data_protocol.md`, a database version, a schema/ETL version, or a query ref.
- `无法独立验证` is a gap, not a pass. It can enter the final output only if the user explicitly accepts the gap and the gap remains visible.
- A final output may cite only artifacts or subtask outputs that passed their required quality gates or are explicitly marked as unresolved gaps.

## Execution Control

- `execution_state.json` exists and has the same `run_id` as `manifest.json`.
- `current_state` is one of `INIT`, `METHOD_LOCKED`, `TASKS_LOCKED`, `EVIDENCE_COMPLETE`, `REVIEWED`, `ACCEPTED`, or `ITERATE`.
- States are unlocked only after the required artifacts for that state exist.
- Resource governance is explicit before execution: run-level resource policy plus per-subtask runtime, memory, large-file, and overflow rules.
- `METHOD_LOCKED` requires frozen method, frozen review expectations, frozen PROSPEC protocol, and frozen structured-data protocol when structured data is required.
- `TASKS_LOCKED` requires every required subtask to define allowed inputs, forbidden inputs, output contract, database access mode, quality gate, merge contract, and resource limits.
- `EVIDENCE_COMPLETE` requires every required subtask to have output refs, plus valid tool-log refs when tools or databases were used.
- `REVIEWED` requires the evidence-bound quality review matrix.
- `ACCEPTED` requires `08_output/minimum_acceptable_output.md` and no unresolved required `需迭代` or `无法独立验证` rows.
- `scripts/validate_execution_control.py <run_folder>` passes before the Agent claims `REVIEWED`, `ACCEPTED`, `质量审查通过`, or `/goal 完成`.

## Resource and Memory Review

- Large files have a declared threshold and read policy before any Agent reads them.
- Unbounded full reads, full row counts, or full in-memory dataframe loads are forbidden for large structured files unless a frozen streaming/database ingestion plan exists.
- Memory overflow, memory pressure pause, process kill, timeout, or resource exhaustion is logged as a failure, not treated as ordinary incompletion.
- Resource failures move the run to `ITERATE` with failed layer, return point, and corrective action.
- Redispatch after resource failure starts from `TASKS_LOCKED` with stricter resource limits.

## Artifact Protocol

- Generated methodology files are stored under a declared output root and run folder.
- `manifest.json` exists and indexes execution state, contract, inputs, structured data protocol, method, PROSPEC protocol, expectations, workflow, subagent dispatch, trace, review, iteration, and final output artifacts.
- The frozen methodology and frozen pre-result review expectations are identifiable.
- The frozen structured-data protocol and PROSPEC execution protocol are identifiable when the task uses structured data or decomposed/parallel Agent execution.
- File statuses are explicit: `draft`, `frozen`, `reviewed`, `superseded`, or `rejected`.
- Later Agents can follow the documented call order without inspecting held-out known results too early.

## Substance Review

- The answer directly addresses the research question.
- Findings are specific enough for medical policy work, not generic policy commentary.
- Claims about effects, costs, access, behavior, equity, or implementation risk are evidence-backed.
- Alternative explanations and major limitations are acknowledged when relevant.
- Recommendations or solutions are linked to identified problems and policy mechanisms.

## Output Review

- The format matches the user's requested artifact.
- The writing separates evidence, interpretation, and recommendation.
- The most important findings are visible without reading every detail.
- The result is usable as a minimum acceptable output: reviewable, reusable, and expandable.

## Iteration Decision

If any required item is `需迭代`, return to the failed layer:

- Contract issue -> redefine research goal or scope.
- Data issue -> collect, clean, verify, or mark missing evidence.
- Structured database issue -> revise the structured-data protocol and rebuild/reload a new database version from governed raw or staging sources.
- Flow issue -> revise the task decomposition.
- PROSPEC issue -> rewrite the affected method/subtask packet before execution or delegation.
- Execution-control issue -> repair the missing state, artifact, tool log, evidence ref, review matrix row, or transition record before advancing.
- Resource issue -> record timeout or memory overflow, add stricter runtime/memory/large-file limits, and redispatch from `TASKS_LOCKED`.
- Knowledge issue -> rebuild entities, relations, tables, graph, or timeline.
- Tool issue -> rerun the right tool or record the failure.
- Substance issue -> revise claims and evidence.
- Output issue -> reformat from accepted findings.

Only mark the task complete after the required quality items pass or the user explicitly accepts the remaining gaps.
