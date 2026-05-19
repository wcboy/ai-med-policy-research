# Artifact Protocol

Use this protocol when an AI-assisted medical policy research task generates, stores, updates, or reuses methodology framework files. If the user only asks for an explanation, keep the answer in chat and do not create files.

## Storage Root

Choose the output root in this order:

1. User-specified path.
2. Existing project governance or research-output directory, if clearly identifiable.
3. `./ai_policy_research_runs` under the current working directory when file output is requested and no path is provided.

Do not store generated methodology files inside raw-data, cleaned-data, validation-data, thesis-chapter, or source-material directories unless the user explicitly requests that target.

## Run Folder

Create a new run folder for each independent methodology or research execution:

```text
<output_root>/<YYYYMMDD-HHMM>-<short-slug>/
```

Do not overwrite a previous run. If revising a prior run, write a new versioned file or append an iteration record.

## Required File Layout

Use this layout unless the user's project already has a stricter convention:

```text
<run_folder>/
  manifest.json
  execution_state.json
  00_contract/research_contract.md
  01_inputs/input_inventory.md
  01_inputs/structured_data_protocol.md
  02_method/methodology_framework.md
  02_method/prospec_execution_protocol.md
  03_expectations/review_expectations.md
  04_workflow/task_decomposition.md
  04_workflow/subagent_dispatch_plan.md
  05_trace/tool_call_log.jsonl
  06_review/quality_review.md
  07_iterations/iteration_log.md
  08_output/minimum_acceptable_output.md
```

Optional files may be added only when useful, for example `knowledge_model.json`, `evidence_table.csv`, `graph_export.json`, or `visualization_notes.md`.

## Manifest Protocol

`manifest.json` is the entry point for later Agents. Keep it machine-readable and update it whenever files are added, frozen, superseded, or reviewed.

Minimum fields:

```json
{
  "run_id": "YYYYMMDD-HHMM-short-slug",
  "skill": "ai-med-policy-research",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp",
  "research_object": "",
  "research_question": "",
  "output_root": "",
  "contamination_boundary": {
    "held_out_known_results": [],
    "held_out_cleaned_data": [],
    "known_result_exposure": "none"
  },
  "artifacts": [
    {
      "path": "02_method/methodology_framework.md",
      "type": "methodology_framework",
      "status": "draft",
      "version": "v1",
      "purpose": ""
    }
  ],
  "structured_data_protocol": {
    "required": false,
    "database_version": "",
    "schema_version": "",
    "cleaning_version": "",
    "label_version": "",
    "storage_path_or_service": "",
    "rebuild_policy": "rebuild_from_raw_or_staging_when_cleaning_ingestion_storage_or_query_design_improves"
  },
  "prospec_protocol": {
    "required": true,
    "frozen": false,
    "parallel_subtasks": [],
    "held_out_results_visible_to_execution_agents": false
  },
  "execution_control": {
    "state_file": "execution_state.json",
    "validator": "scripts/validate_execution_control.py",
    "validator_required_before": ["REVIEWED", "ACCEPTED", "goal_complete"]
  },
  "resource_policy": {
    "required": true,
    "large_file_threshold_mb": 512,
    "large_file_default_policy": "metadata_header_sample_only_unless_streaming_plan_is_frozen",
    "on_timeout_or_memory_overflow": "ITERATE"
  },
  "call_order": [
    "manifest.json",
    "execution_state.json",
    "00_contract/research_contract.md",
    "01_inputs/input_inventory.md",
    "01_inputs/structured_data_protocol.md",
    "03_expectations/review_expectations.md",
    "02_method/methodology_framework.md",
    "02_method/prospec_execution_protocol.md",
    "04_workflow/task_decomposition.md",
    "04_workflow/subagent_dispatch_plan.md",
    "06_review/quality_review.md",
    "07_iterations/iteration_log.md"
  ]
}
```

Allowed artifact statuses:

- `draft`: editable, not yet used for independent verification.
- `frozen`: fixed for execution or independent verification.
- `reviewed`: quality-reviewed against the checklist.
- `superseded`: replaced by a newer version.
- `rejected`: failed review and should not be reused without revision.

## Markdown Artifact Header

Each Markdown artifact should start with a compact header:

```yaml
---
artifact: methodology_framework
run_id: YYYYMMDD-HHMM-short-slug
version: v1
status: draft
created_at: ISO-8601 timestamp
updated_at: ISO-8601 timestamp
known_result_exposure: none
source_scope: raw_inputs_only
---
```

Use `known_result_exposure: none`, `partial`, or `full`. If exposure is `partial` or `full`, state what was seen and do not claim fully independent validation on those materials.

## File Purposes

- `research_contract.md`: research object, question, boundary, expected output, data scope, contamination boundary, and minimum acceptable output.
- `execution_state.json`: machine-checkable state, required artifacts, subtask evidence refs, allowed transitions, quality-gate permissions, and transition log.
- `input_inventory.md`: raw inputs, cleaned inputs, held-out validation artifacts, source dates, paths, and reliability notes.
- `structured_data_protocol.md`: research-need-derived structured-data contract, cleaning rules, label expansion policy, schema, ingestion/storage plan, query/API outputs, validation checks, and database rebuild rule.
- `methodology_framework.md`: frozen or draft method, workflow logic, tool interfaces, data review expectation logic, PROSPEC summary, and self-feedback loop.
- `prospec_execution_protocol.md`: full PROSPEC packet for the overall method and each decomposed subtask: prospective expectations, research boundary, operating procedure, structured data protocol, parallel execution contract, evidence trace, and completion gate.
- `review_expectations.md`: prospective expectations written before results are known, plus human-added expectations with source/time/exposure status.
- `task_decomposition.md`: ordered subtasks with input, method, output, acceptance check, PROSPEC packet reference, dependency, and parallelization status.
- `subagent_dispatch_plan.md`: subagent ownership, read/write scopes, required inputs, forbidden held-out results, database access mode, merge order, conflict rule, and parent-agent review gate.
- `tool_call_log.jsonl`: one JSON object per meaningful tool call or external data access.
- `quality_review.md`: checklist results, failures, return point, and pass/fail decision.
- `iteration_log.md`: each feedback loop and corrective action.
- `minimum_acceptable_output.md`: the smallest reviewable deliverable that passed quality review.

## Execution Control Protocol

Use `execution_state.json` to prevent skipped steps and unsupported quality-review claims. `manifest.json` indexes artifacts; `execution_state.json` decides whether the run may advance.

Minimum schema:

```json
{
  "run_id": "YYYYMMDD-HHMM-short-slug",
  "current_state": "INIT",
  "allowed_next_states": ["METHOD_LOCKED"],
  "required_artifacts": [
    {"path": "00_contract/research_contract.md", "required_for_state": "INIT"}
  ],
  "subtasks": [
    {
      "subtask_id": "S001",
      "required": true,
      "allowed_inputs": [],
      "forbidden_inputs": [],
      "output_contract": "",
      "database_access_mode": "read-only",
      "resource_limits": {
        "max_runtime_seconds": 180,
        "max_memory_mb": 2048,
        "large_file_policy": "metadata_header_sample_only",
        "on_overflow": "ITERATE"
      },
      "requires_tool_log": true,
      "quality_gate": [],
      "merge_contract": "",
      "output_refs": [],
      "tool_log_refs": []
    }
  ],
  "quality_gate": {
    "review_allowed": false,
    "accept_allowed": false
  },
  "resource_policy": {
    "required": true,
    "default_max_runtime_seconds": 180,
    "default_max_memory_mb": 2048,
    "large_file_threshold_mb": 512,
    "large_file_default_policy": "metadata_header_sample_only_unless_streaming_plan_is_frozen",
    "on_memory_overflow": "transition_to_ITERATE_with_failed_layer_return_point_corrective_action"
  },
  "transition_log": []
}
```

Allowed states:

| state | required outputs before entering | unlock condition |
|---|---|---|
| `INIT` | `manifest.json`, `execution_state.json`, `00_contract/research_contract.md`, `01_inputs/input_inventory.md` | contract and held-out boundary exist |
| `METHOD_LOCKED` | frozen `02_method/methodology_framework.md`, frozen `03_expectations/review_expectations.md`, frozen `02_method/prospec_execution_protocol.md`; frozen `01_inputs/structured_data_protocol.md` when structured data is required | method, expectations, PROSPEC, and required data protocol are frozen before observed results are inspected |
| `TASKS_LOCKED` | `04_workflow/task_decomposition.md`, `04_workflow/subagent_dispatch_plan.md` | every required subtask has allowed inputs, forbidden inputs, output contract, quality gate, merge contract, database access mode, and resource limits |
| `EVIDENCE_COMPLETE` | subtask output artifacts and `05_trace/tool_call_log.jsonl` when tools/databases were used | every required subtask has output refs, and tool/database subtasks have valid tool-log refs |
| `REVIEWED` | `06_review/quality_review.md` | every `通过` row in the evidence-bound review matrix cites evidence/tool/artifact/database refs |
| `ACCEPTED` | `08_output/minimum_acceptable_output.md` | all required quality rows pass and `scripts/validate_execution_control.py <run_folder>` exits 0 |
| `ITERATE` | `07_iterations/iteration_log.md` | any required gate fails and the failed layer, return point, and corrective action are recorded |

Do not mark a run `REVIEWED`, `ACCEPTED`, or `/goal 完成` until `scripts/validate_execution_control.py <run_folder>` passes for that state.

## Resource Control

Large structured data must be controlled before dispatch. For each required subtask that may read files, databases, or generated model inputs, define:

- `max_runtime_seconds`
- `max_memory_mb` or an equivalent memory class
- `large_file_policy`
- `on_overflow`, normally `ITERATE`

Default rule: files above `large_file_threshold_mb` must not be fully read, counted, or loaded into memory unless a frozen streaming/database ingestion plan exists. Use file metadata, header inspection, bounded sampling, projected columns, chunked streaming, or database-backed ingestion.

If an Agent pauses, crashes, or stalls due to memory pressure or memory overflow:

1. Stop claiming progress for the affected subtask.
2. Record a tool-log entry with `status: "resource_exhausted"` or `status: "failed"`.
3. Set or keep `execution_state.current_state` as `ITERATE`.
4. Write the failed layer, return point, and corrective action in `07_iterations/iteration_log.md`.
5. Return to `TASKS_LOCKED` before redispatch with stricter resource limits.

## Structured Data Protocol

When structured data is used, `structured_data_protocol.md` must be derived from the research question and expected output before analysis starts. It should specify:

- Research need: analytical grain, target comparisons, required measures, expected output schema, and evidence claims the data must support.
- Cleaning design: source normalization, missingness handling, units, time/geography alignment, entity resolution, deduplication, validation rules, and exclusion rules.
- Label expansion: whether new tags, controlled vocabularies, category mappings, or manual/model labels are needed; record label source, confidence, reviewer, timestamp, and result-exposure status.
- Database design: raw/staging/canonical/derived layers, table schema, primary keys, linkage keys, indexes, views, data dictionary, and provenance fields.
- Ingestion and storage: source snapshot, ETL command or interface, database path/service, schema version, cleaning version, label version, validation outputs, and freeze status.
- Invocation contract: allowed queries, parameters, API/tool entry points, output schema, caching rule, citation/provenance columns, and failure behavior.
- Rebuild rule: if later execution shows that cleaning, labels, ingestion, storage, schema, or query design should change, revise the protocol and rebuild/reload a new database version from raw or staging sources rather than patching the canonical database in place.

If an emergency hotfix is explicitly requested, log it as temporary, keep the hotfixed database separate, and create a follow-up rebuild entry in `iteration_log.md`.

## PROSPEC Execution Protocol

`prospec_execution_protocol.md` keeps methodology decomposition executable by another Agent without leaking known results. Use the packet:

```text
P - Prospective expectations:
R - Research boundary:
O - Operating procedure:
S - Structured data protocol:
P - Parallel execution contract:
E - Evidence trace:
C - Completion gate:
```

For every subtask, include:

- Subtask owner: parent Agent only or named subagent role.
- Inputs allowed: raw/governed files, database views, APIs, screenshots, or references.
- Inputs forbidden: held-out known results, cleaned validation outputs, labels, or prior conclusions that would contaminate execution.
- Output contract: file path, table/view, graph export, memo, or review artifact.
- Database access mode: read-only, rebuild-authorized, write-to-new-version, or no database access.
- Merge contract: how the parent Agent combines outputs, resolves contradictions, and records unsupported claims.
- Quality gate: checklist rows that must pass before the output can be used downstream.

## Tool Call Log Schema

Write one JSON object per line:

```json
{"call_id":"TC0001","time":"ISO-8601 timestamp","subtask_id":"","tool_or_interface":"","input_refs":[],"output_refs":[],"status":"success","notes":""}
```

Use `status` values such as `success`, `failed`, `timeout`, `resource_exhausted`, `non_json`, `partial`, or `skipped`. Record failures instead of silently replacing them with assumptions.

Every non-skipped tool/database/file-parser access that supports a quality-review decision must have a stable `call_id`. Reference it from `execution_state.json` and `quality_review.md` as `call:TC0001`.

## Evidence-Bound Quality Review

`quality_review.md` must include a machine-readable review matrix:

```text
| criterion_id | status | evidence_refs | tool_log_refs | artifact_refs | db_refs | decision_reason |
|---|---|---|---|---|---|---|
| PROSPEC-01 | 通过 | input:I003 | call:TC0007 | 02_method/prospec_execution_protocol.md | db:v1/query:Q002 | 子任务边界完整 |
```

Rules:

- `status` must be `通过`, `需迭代`, or `无法独立验证`.
- A `通过` row must include at least one non-empty `evidence_refs`, `tool_log_refs`, `artifact_refs`, or `db_refs` value.
- Rows involving tool calls, file parsing, web retrieval, databases, statistics, or generated artifacts must cite the relevant `call_id` or artifact path.
- `无法独立验证` does not count as passed. Use `ITERATE` unless the user explicitly accepts the gap and the gap is recorded.

## Call Protocol for Later Agents

A later Agent must load artifacts in this order:

1. Read `manifest.json`.
2. Read `execution_state.json` and confirm the current state and allowed next states.
3. Read `research_contract.md`.
4. Read `input_inventory.md` and identify held-out known results or cleaned validation data.
5. Read `structured_data_protocol.md` before querying or rebuilding any structured database.
6. Read `review_expectations.md` before inspecting observed results.
7. Read `methodology_framework.md` and check whether it is `frozen`.
8. Read `prospec_execution_protocol.md` and confirm the held-out-result boundary.
9. Read `task_decomposition.md` and `subagent_dispatch_plan.md`.
10. Execute or review the workflow.
11. Write or update `tool_call_log.jsonl` with `call_id` values.
12. Update `execution_state.json` with output refs, tool-log refs, gaps, and transition log entries.
13. Write `quality_review.md` with the evidence-bound review matrix.
14. Run `scripts/validate_execution_control.py <run_folder>` before claiming review pass, acceptance, or goal completion.
15. If quality fails, append `iteration_log.md` and create a revised method or database version rather than overwriting the frozen method.

Do not inspect held-out known results before the method and prospective review expectations are frozen.

## Freeze and Revision Protocol

- Freeze `methodology_framework.md` before independent verification.
- Freeze initial `review_expectations.md` before inspecting observed paper/data results.
- Freeze `prospec_execution_protocol.md` before handing the method to execution Agents or subagents.
- Freeze the structured-data protocol before querying canonical analysis outputs. If the protocol changes, create a new database version and mark the older protocol/database as `superseded`.
- Set `execution_state.json.current_state` to `METHOD_LOCKED` only after frozen method, expectations, PROSPEC, and required structured-data protocol exist.
- Set `current_state` to `REVIEWED` or `ACCEPTED` only after the validator passes for the current artifacts.
- Human-added expectations are allowed after freezing, but mark them as `human_added_pre_result` or `human_added_post_exposure`.
- When changing a frozen method, create `methodology_framework.v2.md` or update the status of the old artifact to `superseded` in `manifest.json`.
- Keep the old file available for audit unless the user explicitly asks to remove it.
