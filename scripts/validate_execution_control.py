#!/usr/bin/env python3
"""Validate execution-control artifacts for ai-med-policy-research runs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_STATES = [
    "INIT",
    "METHOD_LOCKED",
    "TASKS_LOCKED",
    "EVIDENCE_COMPLETE",
    "REVIEWED",
    "ACCEPTED",
    "ITERATE",
]
STATE_RANK = {state: index for index, state in enumerate(ALLOWED_STATES)}
ALLOWED_TRANSITIONS = {
    "INIT": {"METHOD_LOCKED", "ITERATE"},
    "METHOD_LOCKED": {"TASKS_LOCKED", "ITERATE"},
    "TASKS_LOCKED": {"EVIDENCE_COMPLETE", "ITERATE"},
    "EVIDENCE_COMPLETE": {"REVIEWED", "ITERATE"},
    "REVIEWED": {"ACCEPTED", "ITERATE"},
    "ITERATE": {"INIT", "METHOD_LOCKED", "TASKS_LOCKED", "EVIDENCE_COMPLETE"},
}
REVIEW_COLUMNS = {
    "criterion_id",
    "status",
    "evidence_refs",
    "tool_log_refs",
    "artifact_refs",
    "db_refs",
    "decision_reason",
}
RAW_SNAPSHOT_COLUMNS = {
    "raw_id",
    "path",
    "format",
    "size_or_rows",
    "coverage_status",
    "inspection_method",
    "tool_log_refs",
    "notes",
}
PROSPEC_TASK_FIELDS = {
    "subtask_id",
    "prospective_expectations",
    "research_boundary",
    "operating_procedure",
    "structured_data_protocol",
    "parallel_execution_contract",
    "evidence_trace",
    "completion_gate",
}
NON_PASS_TOOL_STATUSES = {
    "failed",
    "failure",
    "error",
    "timeout",
    "resource_exhausted",
    "memory_exhausted",
    "non_json",
    "partial",
    "skipped",
}
PASS = "通过"
ITERATE = "需迭代"
UNVERIFIABLE = "无法独立验证"
EMPTY_VALUES = {"", "-", "--", "na", "n/a", "none", "null", "[]"}


class Validator:
    def __init__(self, run_folder: Path) -> None:
        self.run_folder = run_folder
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.manifest: dict[str, Any] = {}
        self.state: dict[str, Any] = {}
        self.call_ids: set[str] = set()
        self.tool_records: dict[str, dict[str, Any]] = {}
        self.review_rows: list[dict[str, str]] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def load(self) -> None:
        self.manifest = self.load_json("manifest.json")
        self.state = self.load_json("execution_state.json")

    def load_json(self, rel_path: str) -> dict[str, Any]:
        path = self.run_folder / rel_path
        if not path.exists():
            self.error(f"missing required file: {rel_path}")
            return {}
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:  # noqa: BLE001 - validator should report parse failures.
            self.error(f"invalid JSON in {rel_path}: {exc}")
            return {}
        if not isinstance(data, dict):
            self.error(f"{rel_path} must contain a JSON object")
            return {}
        return data

    def exists(self, rel_path: str) -> bool:
        return (self.run_folder / rel_path).exists()

    def text(self, rel_path: str) -> str:
        path = self.run_folder / rel_path
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")

    def current_state(self) -> str:
        return str(self.state.get("current_state", ""))

    def reached(self, state: str) -> bool:
        current = self.current_state()
        if current == "ITERATE":
            return state in {"INIT", "METHOD_LOCKED", "TASKS_LOCKED", "EVIDENCE_COMPLETE", "REVIEWED", "ITERATE"}
        return STATE_RANK.get(current, -1) >= STATE_RANK[state]

    def validate(self) -> int:
        self.load()
        self.validate_run_id()
        self.validate_state()
        self.validate_transition_log()
        self.validate_manifest_call_order()
        self.validate_source_identity_blinding()
        self.validate_required_artifacts_from_state()
        self.validate_init_files()
        self.validate_raw_data_snapshot()
        self.validate_method_locked()
        self.validate_tasks_locked()
        self.validate_resource_policy()
        self.load_tool_log()
        self.validate_evidence_complete()
        self.validate_quality_review()
        self.validate_quality_gate_permissions()
        self.validate_final_state()
        return 1 if self.errors else 0

    def validate_run_id(self) -> None:
        manifest_run_id = self.manifest.get("run_id")
        state_run_id = self.state.get("run_id")
        if not manifest_run_id:
            self.error("manifest.json missing run_id")
        if not state_run_id:
            self.error("execution_state.json missing run_id")
        if manifest_run_id and state_run_id and manifest_run_id != state_run_id:
            self.error(f"run_id mismatch: manifest={manifest_run_id!r}, state={state_run_id!r}")

    def validate_state(self) -> None:
        current = self.current_state()
        if current not in ALLOWED_STATES:
            self.error(f"invalid current_state: {current!r}")
        next_states = self.state.get("allowed_next_states", [])
        if next_states and not isinstance(next_states, list):
            self.error("allowed_next_states must be a list")
            return
        for next_state in next_states:
            if next_state not in ALLOWED_STATES:
                self.error(f"invalid allowed_next_states entry: {next_state!r}")

    def validate_transition_log(self) -> None:
        current = self.current_state()
        if current not in ALLOWED_STATES:
            return
        transition_log = self.state.get("transition_log", [])
        if transition_log in (None, ""):
            transition_log = []
        if not isinstance(transition_log, list):
            self.error("execution_state.transition_log must be a list")
            return
        if current != "INIT" and not transition_log:
            self.error(f"{current} requires non-empty transition_log")
            return
        last_to = "INIT"
        for index, entry in enumerate(transition_log, start=1):
            if not isinstance(entry, dict):
                self.error(f"transition_log entry #{index} must be an object")
                continue
            from_state = transition_value(entry, "from")
            to_state = transition_value(entry, "to")
            if from_state not in ALLOWED_STATES:
                self.error(f"transition_log entry #{index} has invalid from state: {from_state!r}")
                continue
            if to_state not in ALLOWED_STATES:
                self.error(f"transition_log entry #{index} has invalid to state: {to_state!r}")
                continue
            if index == 1 and from_state != "INIT":
                self.error(f"transition_log entry #1 must start from INIT, found {from_state!r}")
            if index > 1 and from_state != last_to:
                self.error(f"transition_log entry #{index} starts from {from_state!r}, expected {last_to!r}")
            if to_state not in ALLOWED_TRANSITIONS.get(from_state, set()):
                self.error(f"invalid transition_log jump: {from_state} -> {to_state}")
            for field in ["time", "reason", "artifact_refs"]:
                if not has_value(entry.get(field, "")):
                    self.error(f"transition_log entry #{index} missing {field}")
            last_to = to_state
        if transition_log and last_to != current:
            self.error(f"transition_log last to state {last_to!r} does not match current_state {current!r}")

    def validate_manifest_call_order(self) -> None:
        call_order = self.manifest.get("call_order", [])
        if call_order and "execution_state.json" not in call_order:
            self.error("manifest.call_order must include execution_state.json")
        if call_order and self.raw_data_snapshot_required():
            inventory_path = self.raw_data_inventory_path()
            if inventory_path not in call_order:
                self.error(f"manifest.call_order must include {inventory_path} when raw_data_snapshot.required is true")
            path = self.raw_data_snapshot_path()
            if path not in call_order:
                self.error(f"manifest.call_order must include {path} when raw_data_snapshot.required is true")

    def validate_source_identity_blinding(self) -> None:
        config = self.manifest.get("source_identity_blinding", {})
        if not config:
            return
        if not isinstance(config, dict):
            self.error("manifest.source_identity_blinding must be an object when present")
            return
        if not bool(config.get("required")):
            return

        if not bool(config.get("execution_agent_blind")):
            self.error("source_identity_blinding.required requires execution_agent_blind=true")
        if not bool(config.get("forbidden_external_lookup")):
            self.error("source_identity_blinding.required requires forbidden_external_lookup=true")

        for field in [
            "restricted_identity_artifact",
            "restricted_scan_terms_artifact",
            "public_leakage_report",
            "blinded_source_ids",
            "forbidden_identity_fields",
        ]:
            self.require_field(config, field, "manifest.source_identity_blinding")

        restricted = str(config.get("restricted_identity_artifact", "")).strip()
        restricted_terms = str(config.get("restricted_scan_terms_artifact", "")).strip()
        call_order = self.manifest.get("call_order", [])
        if restricted and isinstance(call_order, list) and restricted in call_order:
            self.error(f"restricted identity artifact must not be in manifest.call_order: {restricted}")
        if restricted_terms and isinstance(call_order, list) and restricted_terms in call_order:
            self.error(f"restricted scan terms artifact must not be in manifest.call_order: {restricted_terms}")

        terms_value = config.get("forbidden_identity_terms", [])
        if has_value(terms_value):
            self.error("manifest.source_identity_blinding must not contain public forbidden_identity_terms; use restricted_scan_terms_artifact")

        terms = self.load_identity_scan_terms(restricted_terms)
        scan_paths = self.public_identity_scan_paths({restricted, restricted_terms})
        for term in terms:
            if len(term) < 4:
                self.warn(f"source identity term is too short for reliable leakage scan: {redact_term(term)}")
                continue
            lowered_term = term.casefold()
            for rel_path in scan_paths:
                text = self.text(rel_path)
                if text and lowered_term in text.casefold():
                    self.error(f"{rel_path} contains forbidden source identity term: {redact_term(term)}")
        self.validate_leakage_report(config.get("public_leakage_report", ""))
        self.validate_execution_package(config, {restricted, restricted_terms})

    def load_identity_scan_terms(self, rel_path: str) -> list[str]:
        if not rel_path:
            return []
        data = self.load_json(rel_path)
        value = data.get("forbidden_identity_terms", data.get("terms", []))
        if not isinstance(value, list):
            self.error(f"{rel_path} forbidden_identity_terms must be a list")
            return []
        terms = [str(term).strip() for term in value if str(term).strip()]
        if not terms:
            self.error(f"{rel_path} must contain forbidden_identity_terms for leakage scanning")
        return terms

    def validate_leakage_report(self, rel_path: Any) -> None:
        report_path = str(rel_path or "").strip()
        if not report_path or not self.exists(report_path):
            return
        report = self.load_json(report_path)
        for forbidden_key in ["forbidden_identity_terms", "terms", "raw_terms", "identity_terms"]:
            if has_value(report.get(forbidden_key, "")):
                self.error(f"{report_path} must not expose {forbidden_key}; keep exact terms restricted")

    def validate_execution_package(self, config: dict[str, Any], restricted_paths: set[str]) -> None:
        package_path = str(config.get("execution_package_path", "") or "").strip()
        if not package_path:
            return
        package_root = self.run_folder / package_path
        if not package_root.exists() or not package_root.is_dir():
            return
        restricted_names = {Path(path).name for path in restricted_paths if path}
        for path in package_root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(self.run_folder).as_posix()
            if path.name in restricted_names:
                self.error(f"execution package contains restricted identity artifact: {rel}")

    def public_identity_scan_paths(self, restricted_paths: set[str]) -> list[str]:
        excluded = {
            "",
            *restricted_paths,
        }
        candidates = {
            "manifest.json",
            "execution_state.json",
            "00_contract/research_contract.md",
            "01_inputs/input_inventory.md",
            "01_inputs/raw_inventory.json",
            "01_inputs/README_DATA.md",
            "01_inputs/structured_data_protocol.md",
            "02_method/methodology_framework.md",
            "02_method/prospec_execution_protocol.md",
            "03_expectations/review_expectations.md",
            "04_workflow/task_decomposition.md",
            "04_workflow/prospec_tasks.json",
            "04_workflow/subagent_dispatch_plan.md",
            "05_trace/tool_call_log.jsonl",
            "06_review/source_identity_leakage_report.json",
            "06_review/quality_review.md",
            "07_iterations/iteration_log.md",
            "08_output/minimum_acceptable_output.md",
        }
        call_order = self.manifest.get("call_order", [])
        if isinstance(call_order, list):
            candidates.update(str(path) for path in call_order)
        for artifact in self.manifest.get("artifacts", []) or []:
            if isinstance(artifact, dict) and artifact.get("path"):
                candidates.add(str(artifact["path"]))
        return sorted(path for path in candidates if path not in excluded and self.exists(path))

    def validate_required_artifacts_from_state(self) -> None:
        artifacts = self.state.get("required_artifacts", [])
        if artifacts in (None, ""):
            return
        if not isinstance(artifacts, list):
            self.error("execution_state.required_artifacts must be a list")
            return
        for item in artifacts:
            if isinstance(item, str):
                rel_path = item
            elif isinstance(item, dict):
                rel_path = str(item.get("path", ""))
            else:
                self.error("required_artifacts entries must be strings or objects")
                continue
            if rel_path and not self.exists(rel_path):
                self.error(f"required artifact missing: {rel_path}")

    def validate_init_files(self) -> None:
        if not self.reached("INIT"):
            return
        for rel_path in [
            "00_contract/research_contract.md",
            "01_inputs/input_inventory.md",
        ]:
            if not self.exists(rel_path):
                self.error(f"INIT requires {rel_path}")
        if self.raw_data_snapshot_required():
            inventory_path = self.raw_data_inventory_path()
            if not self.exists(inventory_path):
                self.error(f"INIT requires {inventory_path} when raw_data_snapshot.required is true")
            rel_path = self.raw_data_snapshot_path()
            if not self.exists(rel_path):
                self.error(f"INIT requires {rel_path} when raw_data_snapshot.required is true")

    def validate_raw_data_snapshot(self) -> None:
        if not self.raw_data_snapshot_required():
            return
        inventory_path = self.raw_data_inventory_path()
        raw_inputs = self.load_raw_inventory(inventory_path)
        rel_path = self.raw_data_snapshot_path()
        if not self.exists(rel_path):
            return

        text = self.text(rel_path)
        rows = parse_table_with_columns(text, RAW_SNAPSHOT_COLUMNS)
        if not rows:
            self.error(f"{rel_path} missing RAW Data Coverage Matrix with required columns")
            return

        expected_count = self.raw_data_expected_count()
        if raw_inputs:
            expected_count = max(expected_count, len(raw_inputs))
        if expected_count and len(rows) < expected_count:
            self.error(f"{rel_path} covers {len(rows)} raw inputs but manifest expects {expected_count}")

        rows_by_raw_id = {normalize_key(row.get("raw_id", "")): row for row in rows if has_value(row.get("raw_id", ""))}
        rows_by_path = {normalize_path_key(row.get("path", "")): row for row in rows if has_value(row.get("path", ""))}
        for item in raw_inputs:
            raw_id = normalize_key(item.get("raw_id", ""))
            raw_path = normalize_path_key(item.get("path", ""))
            if raw_id not in rows_by_raw_id and raw_path not in rows_by_path:
                self.error(f"{rel_path} missing inventory raw input: {item.get('raw_id') or item.get('path')}")

        for index, row in enumerate(rows, start=1):
            raw_id = row.get("raw_id") or f"row {index}"
            for field in ["raw_id", "path", "format", "coverage_status", "inspection_method"]:
                if not has_value(row.get(field, "")):
                    self.error(f"{rel_path} {raw_id} missing {field}")
            status = normalize_status(row.get("coverage_status", ""))
            if self.reached("METHOD_LOCKED") and status in {
                "",
                "uninspected",
                "not_inspected",
                "not inspected",
                "skipped",
                "skip",
                "todo",
                "tbd",
                "unknown",
                "unknown_status",
                "partial",
                "partially_inspected",
                "partially inspected",
                "unreadable",
                "failed",
                "未知",
                "待补",
            }:
                self.error(f"{rel_path} {raw_id} has blocking coverage_status before METHOD_LOCKED: {row.get('coverage_status', '')!r}")

    def validate_method_locked(self) -> None:
        if not self.reached("METHOD_LOCKED"):
            return
        for rel_path in [
            "02_method/methodology_framework.md",
            "03_expectations/review_expectations.md",
            "02_method/prospec_execution_protocol.md",
        ]:
            self.require_frozen(rel_path)

        structured_required = bool(self.manifest.get("structured_data_protocol", {}).get("required"))
        if self.raw_data_snapshot_required():
            self.require_frozen(self.raw_data_inventory_path())
            self.require_frozen(self.raw_data_snapshot_path())
        if structured_required:
            self.require_frozen("01_inputs/structured_data_protocol.md")

    def raw_data_snapshot_required(self) -> bool:
        config = self.manifest.get("raw_data_snapshot", {})
        return isinstance(config, dict) and bool(config.get("required"))

    def raw_data_snapshot_path(self) -> str:
        config = self.manifest.get("raw_data_snapshot", {})
        if isinstance(config, dict) and has_value(config.get("path", "")):
            return str(config.get("path"))
        return "01_inputs/README_DATA.md"

    def raw_data_inventory_path(self) -> str:
        config = self.manifest.get("raw_data_snapshot", {})
        if isinstance(config, dict) and has_value(config.get("raw_inventory_path", "")):
            return str(config.get("raw_inventory_path"))
        return "01_inputs/raw_inventory.json"

    def load_raw_inventory(self, rel_path: str) -> list[dict[str, Any]]:
        if not self.exists(rel_path):
            return []
        data = self.load_json(rel_path)
        raw_inputs = data.get("raw_inputs", [])
        if not isinstance(raw_inputs, list) or not raw_inputs:
            self.error(f"{rel_path} requires non-empty raw_inputs list")
            return []
        valid_inputs: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_paths: set[str] = set()
        for index, item in enumerate(raw_inputs, start=1):
            if not isinstance(item, dict):
                self.error(f"{rel_path} raw_inputs[{index}] must be an object")
                continue
            for field in ["raw_id", "path", "format", "source_type", "detected_by"]:
                self.require_field(item, field, f"{rel_path} raw_inputs[{index}]")
            raw_id = normalize_key(item.get("raw_id", ""))
            raw_path = normalize_path_key(item.get("path", ""))
            if raw_id:
                if raw_id in seen_ids:
                    self.error(f"{rel_path} duplicate raw_id: {item.get('raw_id')}")
                seen_ids.add(raw_id)
            if raw_path:
                if raw_path in seen_paths:
                    self.error(f"{rel_path} duplicate path: {item.get('path')}")
                seen_paths.add(raw_path)
            valid_inputs.append(item)
        return valid_inputs

    def raw_data_expected_count(self) -> int:
        config = self.manifest.get("raw_data_snapshot", {})
        if not isinstance(config, dict):
            return 0
        value = config.get("expected_raw_input_count", 0)
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            self.error("manifest.raw_data_snapshot.expected_raw_input_count must be an integer")
            return 0

    def validate_tasks_locked(self) -> None:
        if not self.reached("TASKS_LOCKED"):
            return
        for rel_path in [
            "04_workflow/task_decomposition.md",
            "04_workflow/subagent_dispatch_plan.md",
        ]:
            if not self.exists(rel_path):
                self.error(f"TASKS_LOCKED requires {rel_path}")
        prospec_tasks = self.load_prospec_tasks()

        subtasks = self.state.get("subtasks", [])
        if not isinstance(subtasks, list) or not subtasks:
            self.error("TASKS_LOCKED requires execution_state.subtasks with at least one subtask")
            return
        for index, subtask in enumerate(subtasks, start=1):
            if not isinstance(subtask, dict):
                self.error(f"subtask #{index} must be an object")
                continue
            subtask_id = subtask.get("subtask_id") or f"#{index}"
            self.require_field(subtask, "subtask_id", f"subtask {subtask_id}")
            self.require_field(subtask, "allowed_inputs", f"subtask {subtask_id}")
            if "forbidden_inputs" not in subtask:
                self.error(f"subtask {subtask_id} missing forbidden_inputs")
            self.require_field(subtask, "output_contract", f"subtask {subtask_id}")
            self.require_field(subtask, "database_access_mode", f"subtask {subtask_id}")
            self.require_field(subtask, "quality_gate", f"subtask {subtask_id}")
            self.require_field(subtask, "merge_contract", f"subtask {subtask_id}")
            if subtask.get("required", True) is not False:
                self.validate_subtask_prospec_packet(str(subtask_id), prospec_tasks)

    def prospec_tasks_path(self) -> str:
        config = self.manifest.get("prospec_protocol", {})
        if isinstance(config, dict) and has_value(config.get("tasks_path", "")):
            return str(config.get("tasks_path"))
        return "04_workflow/prospec_tasks.json"

    def load_prospec_tasks(self) -> dict[str, dict[str, Any]]:
        config = self.manifest.get("prospec_protocol", {})
        if isinstance(config, dict) and not bool(config.get("required", True)):
            return {}
        rel_path = self.prospec_tasks_path()
        if not self.exists(rel_path):
            self.error(f"TASKS_LOCKED requires {rel_path} when prospec_protocol.required is true")
            return {}
        data = self.load_json(rel_path)
        tasks_value = data.get("tasks", [])
        if isinstance(tasks_value, dict):
            task_items = list(tasks_value.values())
        elif isinstance(tasks_value, list):
            task_items = tasks_value
        else:
            self.error(f"{rel_path} tasks must be a list or object")
            return {}
        tasks: dict[str, dict[str, Any]] = {}
        for index, task in enumerate(task_items, start=1):
            if not isinstance(task, dict):
                self.error(f"{rel_path} tasks[{index}] must be an object")
                continue
            subtask_id = str(task.get("subtask_id", "")).strip()
            if not subtask_id:
                self.error(f"{rel_path} tasks[{index}] missing subtask_id")
                continue
            tasks[subtask_id] = task
        return tasks

    def validate_subtask_prospec_packet(self, subtask_id: str, prospec_tasks: dict[str, dict[str, Any]]) -> None:
        if not prospec_tasks:
            return
        packet = prospec_tasks.get(subtask_id)
        if not packet:
            self.error(f"subtask {subtask_id} missing matching PROSPEC packet in {self.prospec_tasks_path()}")
            return
        for field in PROSPEC_TASK_FIELDS:
            if not has_value(packet.get(field, "")):
                self.error(f"PROSPEC packet {subtask_id} missing {field}")

    def validate_resource_policy(self) -> None:
        if not self.reached("TASKS_LOCKED"):
            return
        policy = self.state.get("resource_policy", {})
        if not isinstance(policy, dict):
            self.error("execution_state.resource_policy must be an object when present")
            return
        required = bool(policy.get("required"))
        if not required:
            return
        for field in [
            "default_max_runtime_seconds",
            "default_max_memory_mb",
            "large_file_threshold_mb",
            "large_file_default_policy",
            "on_memory_overflow",
        ]:
            self.require_field(policy, field, "execution_state.resource_policy")

        subtasks = self.state.get("subtasks", [])
        if not isinstance(subtasks, list):
            return
        for index, subtask in enumerate(subtasks, start=1):
            if not isinstance(subtask, dict) or subtask.get("required", True) is False:
                continue
            subtask_id = subtask.get("subtask_id") or f"#{index}"
            limits = subtask.get("resource_limits")
            if not isinstance(limits, dict):
                self.error(f"required subtask {subtask_id} missing resource_limits")
                continue
            for field in [
                "max_runtime_seconds",
                "max_memory_mb",
                "large_file_policy",
                "on_overflow",
            ]:
                self.require_field(limits, field, f"subtask {subtask_id} resource_limits")

    def load_tool_log(self) -> None:
        path = self.run_folder / "05_trace/tool_call_log.jsonl"
        if not path.exists():
            return
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                self.error(f"invalid JSONL at 05_trace/tool_call_log.jsonl:{line_number}: {exc}")
                continue
            call_id = record.get("call_id")
            if not call_id:
                self.error(f"tool log line {line_number} missing call_id")
                continue
            call_id = str(call_id)
            if call_id in self.call_ids:
                self.error(f"duplicate call_id in tool log: {call_id}")
            self.call_ids.add(call_id)
            self.tool_records[call_id] = record
            if not record.get("subtask_id"):
                self.warn(f"tool log {call_id} missing subtask_id")
            if not record.get("status"):
                self.error(f"tool log {call_id} missing status")

    def validate_evidence_complete(self) -> None:
        if not self.reached("EVIDENCE_COMPLETE"):
            return
        subtasks = self.state.get("subtasks", [])
        if not isinstance(subtasks, list) or not subtasks:
            self.error("EVIDENCE_COMPLETE requires execution_state.subtasks")
            return

        for index, subtask in enumerate(subtasks, start=1):
            if not isinstance(subtask, dict):
                continue
            if subtask.get("required", True) is False:
                continue
            subtask_id = subtask.get("subtask_id") or f"#{index}"
            output_refs = subtask.get("output_refs", [])
            if not has_value(output_refs):
                self.error(f"required subtask {subtask_id} missing output_refs")
            else:
                self.validate_artifact_refs(output_refs, f"subtask {subtask_id} output_refs")

            requires_tool = bool(subtask.get("requires_tool_log"))
            database_mode = str(subtask.get("database_access_mode", "")).strip().lower()
            if database_mode and database_mode not in {"no database access", "none", "no_database_access"}:
                requires_tool = True
            if requires_tool:
                tool_refs = subtask.get("tool_log_refs", [])
                if not has_value(tool_refs):
                    self.error(f"required subtask {subtask_id} missing tool_log_refs")
                else:
                    self.validate_call_refs(tool_refs, f"subtask {subtask_id} tool_log_refs")
                    self.validate_success_call_refs(tool_refs, f"subtask {subtask_id} tool_log_refs")

    def validate_quality_review(self) -> None:
        if not self.reached("REVIEWED") and self.current_state() != "ITERATE":
            return
        rel_path = "06_review/quality_review.md"
        if not self.exists(rel_path):
            self.error(f"{self.current_state()} requires {rel_path}")
            return
        self.review_rows = parse_review_matrix(self.text(rel_path))
        if not self.review_rows:
            self.error("quality_review.md missing evidence-bound review matrix")
            return
        for row in self.review_rows:
            criterion = row.get("criterion_id", "<missing criterion_id>")
            status = normalize_cell(row.get("status", ""))
            if status not in {PASS, ITERATE, UNVERIFIABLE}:
                self.error(f"quality review {criterion} has invalid status: {status!r}")
                continue
            if status == PASS:
                refs = [
                    row.get("evidence_refs", ""),
                    row.get("tool_log_refs", ""),
                    row.get("artifact_refs", ""),
                    row.get("db_refs", ""),
                ]
                if not any(has_value(ref) for ref in refs):
                    self.error(f"quality review {criterion} marked 通过 without evidence/tool/artifact/db refs")
                self.validate_success_call_refs(row.get("tool_log_refs", ""), f"quality review {criterion} tool_log_refs")
            self.validate_call_refs(row.get("tool_log_refs", ""), f"quality review {criterion} tool_log_refs")
            self.validate_artifact_refs(row.get("artifact_refs", ""), f"quality review {criterion} artifact_refs")

    def validate_quality_gate_permissions(self) -> None:
        current = self.current_state()
        quality_gate = self.state.get("quality_gate", {})
        if not isinstance(quality_gate, dict):
            if current in {"REVIEWED", "ACCEPTED"}:
                self.error("execution_state.quality_gate must be an object before REVIEWED or ACCEPTED")
            return
        if current in {"REVIEWED", "ACCEPTED"} and not bool(quality_gate.get("review_allowed")):
            self.error(f"{current} requires quality_gate.review_allowed=true")
        if current == "ACCEPTED" and not bool(quality_gate.get("accept_allowed")):
            self.error("ACCEPTED requires quality_gate.accept_allowed=true")

    def validate_final_state(self) -> None:
        current = self.current_state()
        if current == "ACCEPTED":
            if not self.exists("08_output/minimum_acceptable_output.md"):
                self.error("ACCEPTED requires 08_output/minimum_acceptable_output.md")
            for row in self.review_rows:
                status = normalize_cell(row.get("status", ""))
                if status != PASS:
                    criterion = row.get("criterion_id", "<missing criterion_id>")
                    self.error(f"ACCEPTED cannot include unresolved quality row {criterion}: {status}")
        if current == "ITERATE" or any(normalize_cell(row.get("status", "")) == ITERATE for row in self.review_rows):
            rel_path = "07_iterations/iteration_log.md"
            if not self.exists(rel_path):
                self.error("ITERATE or 需迭代 quality rows require 07_iterations/iteration_log.md")
            else:
                text = self.text(rel_path).lower()
                required_groups = [
                    ("failed layer", "failed_layer", "失败层"),
                    ("return point", "return_point", "返回"),
                    ("corrective action", "corrective_action", "纠正", "修正"),
                ]
                for group in required_groups:
                    if not any(token in text for token in group):
                        self.error(f"iteration_log.md missing one of: {', '.join(group)}")

    def require_frozen(self, rel_path: str) -> None:
        if not self.exists(rel_path):
            self.error(f"METHOD_LOCKED requires {rel_path}")
            return
        status = self.artifact_status(rel_path)
        if status != "frozen":
            self.error(f"{rel_path} must be frozen before METHOD_LOCKED; found {status or 'missing status'}")

    def artifact_status(self, rel_path: str) -> str:
        for artifact in self.manifest.get("artifacts", []) or []:
            if isinstance(artifact, dict) and artifact.get("path") == rel_path and artifact.get("status"):
                return str(artifact["status"]).strip()
        header = frontmatter(self.text(rel_path))
        if "status" in header:
            return header["status"].strip()
        return ""

    def require_field(self, data: dict[str, Any], field: str, label: str) -> None:
        if field not in data:
            self.error(f"{label} missing {field}")
            return
        if not has_value(data[field]):
            self.error(f"{label} has empty {field}")

    def validate_call_refs(self, refs: Any, label: str) -> None:
        for call_id in call_refs(refs):
            if call_id not in self.call_ids:
                self.error(f"{label} references missing call_id: {call_id}")

    def validate_success_call_refs(self, refs: Any, label: str) -> None:
        for call_id in call_refs(refs):
            record = self.tool_records.get(call_id)
            if not record:
                continue
            status = normalize_status(record.get("status", ""))
            if status in NON_PASS_TOOL_STATUSES or status != "success":
                self.error(f"{label} references non-success call_id {call_id}: {status or 'missing status'}")

    def validate_artifact_refs(self, refs: Any, label: str) -> None:
        for ref in split_refs(refs):
            rel_path = artifact_ref_to_path(ref)
            if not rel_path:
                continue
            if looks_like_file_ref(rel_path) and not self.exists(rel_path):
                self.error(f"{label} references missing artifact: {rel_path}")

    def report(self, exit_code: int) -> None:
        payload = {
            "run_folder": str(self.run_folder),
            "current_state": self.current_state() or None,
            "status": "valid" if exit_code == 0 else "invalid",
            "errors": self.errors,
            "warnings": self.warnings,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    header: dict[str, str] = {}
    for raw_line in text[4:end].splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        header[key.strip()] = value.strip().strip('"').strip("'")
    return header


def parse_review_matrix(text: str) -> list[dict[str, str]]:
    return parse_table_with_columns(text, REVIEW_COLUMNS)


def parse_table_with_columns(text: str, required_columns: set[str]) -> list[dict[str, str]]:
    lines = text.splitlines()
    rows: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        columns = parse_table_line(line)
        if not columns:
            continue
        normalized = [column.strip().lower() for column in columns]
        if not required_columns.issubset(set(normalized)):
            continue
        if index + 1 >= len(lines) or not is_separator_line(lines[index + 1]):
            continue
        positions = {column: normalized.index(column) for column in required_columns}
        for row_line in lines[index + 2 :]:
            cells = parse_table_line(row_line)
            if not cells:
                break
            if len(cells) < len(normalized):
                cells.extend([""] * (len(normalized) - len(cells)))
            rows.append({column: cells[position].strip() for column, position in positions.items()})
        break
    return rows


def parse_table_line(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def is_separator_line(line: str) -> bool:
    cells = parse_table_line(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def normalize_cell(value: Any) -> str:
    return str(value).strip()


def normalize_status(value: Any) -> str:
    return str(value).strip().lower()


def transition_value(entry: dict[str, Any], key: str) -> str:
    for candidate in [key, f"{key}_state"]:
        value = entry.get(candidate)
        if has_value(value):
            return str(value).strip()
    return ""


def normalize_key(value: Any) -> str:
    return str(value).strip().casefold()


def normalize_path_key(value: Any) -> str:
    return str(value).strip().replace("\\", "/").rstrip("/").casefold()


def redact_term(term: str) -> str:
    cleaned = str(term)
    return f"<redacted:{len(cleaned)} chars>"


def has_value(value: Any) -> bool:
    if isinstance(value, list):
        return any(has_value(item) for item in value)
    if isinstance(value, dict):
        return bool(value)
    return str(value).strip().lower() not in EMPTY_VALUES


def split_refs(value: Any) -> list[str]:
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(split_refs(item))
        return refs
    raw = str(value).strip()
    if raw.lower() in EMPTY_VALUES:
        return []
    parts = re.split(r"[;,]\s*|\s{2,}", raw)
    refs: list[str] = []
    for part in parts:
        cleaned = part.strip()
        if cleaned and cleaned.lower() not in EMPTY_VALUES:
            refs.append(cleaned)
    return refs


def call_refs(value: Any) -> list[str]:
    raw = " ".join(split_refs(value)) if isinstance(value, list) else str(value)
    return re.findall(r"\bcall:([A-Za-z0-9_.-]+)\b", raw)


def artifact_ref_to_path(ref: str) -> str:
    cleaned = ref.strip()
    if not cleaned or cleaned.lower() in EMPTY_VALUES:
        return ""
    if cleaned.startswith("artifact:"):
        cleaned = cleaned.split(":", 1)[1]
    if cleaned.startswith(("call:", "db:", "input:", "evidence:", "url:", "http://", "https://")):
        return ""
    return cleaned


def looks_like_file_ref(ref: str) -> bool:
    suffixes = (
        ".md",
        ".json",
        ".jsonl",
        ".csv",
        ".tsv",
        ".txt",
        ".yaml",
        ".yml",
        ".html",
        ".png",
        ".svg",
        ".xlsx",
        ".docx",
        ".pdf",
    )
    return "/" in ref or ref.endswith(suffixes)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_folder", help="Path to a generated ai-med-policy-research run folder")
    args = parser.parse_args(argv)

    run_folder = Path(args.run_folder).resolve()
    validator = Validator(run_folder)
    if not run_folder.exists() or not run_folder.is_dir():
        validator.error(f"run_folder does not exist or is not a directory: {run_folder}")
        validator.report(1)
        return 1

    exit_code = validator.validate()
    validator.report(exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
