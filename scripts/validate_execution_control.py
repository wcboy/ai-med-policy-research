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
REVIEW_COLUMNS = {
    "criterion_id",
    "status",
    "evidence_refs",
    "tool_log_refs",
    "artifact_refs",
    "db_refs",
    "decision_reason",
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
        self.validate_manifest_call_order()
        self.validate_required_artifacts_from_state()
        self.validate_init_files()
        self.validate_method_locked()
        self.validate_tasks_locked()
        self.validate_resource_policy()
        self.load_tool_log()
        self.validate_evidence_complete()
        self.validate_quality_review()
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

    def validate_manifest_call_order(self) -> None:
        call_order = self.manifest.get("call_order", [])
        if call_order and "execution_state.json" not in call_order:
            self.error("manifest.call_order must include execution_state.json")

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
        if structured_required:
            self.require_frozen("01_inputs/structured_data_protocol.md")

    def validate_tasks_locked(self) -> None:
        if not self.reached("TASKS_LOCKED"):
            return
        for rel_path in [
            "04_workflow/task_decomposition.md",
            "04_workflow/subagent_dispatch_plan.md",
        ]:
            if not self.exists(rel_path):
                self.error(f"TASKS_LOCKED requires {rel_path}")

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
            self.call_ids.add(str(call_id))
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
            self.validate_call_refs(row.get("tool_log_refs", ""), f"quality review {criterion} tool_log_refs")
            self.validate_artifact_refs(row.get("artifact_refs", ""), f"quality review {criterion} artifact_refs")

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
    lines = text.splitlines()
    rows: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        columns = parse_table_line(line)
        if not columns:
            continue
        normalized = [column.strip().lower() for column in columns]
        if not REVIEW_COLUMNS.issubset(set(normalized)):
            continue
        if index + 1 >= len(lines) or not is_separator_line(lines[index + 1]):
            continue
        positions = {column: normalized.index(column) for column in REVIEW_COLUMNS}
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
