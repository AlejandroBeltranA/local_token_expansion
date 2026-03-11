#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Derive drift_v0 failure-cause CSVs from evaluated JSONL artifacts."
    )
    parser.add_argument("--input", required=True, help="Evaluated JSONL input.")
    parser.add_argument("--output-by-model", required=True, help="CSV output grouped by model.")
    parser.add_argument("--output-overall", required=True, help="CSV output aggregated overall.")
    parser.add_argument(
        "--near-cap-threshold",
        type=float,
        default=0.95,
        help="Treat outputs at or above this fraction of max_tokens as near-cap.",
    )
    parser.add_argument(
        "--default-max-tokens",
        type=int,
        default=256,
        help="Fallback max_tokens when a row does not include it.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as infile:
        for line in infile:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def is_primary(row: dict[str, Any]) -> bool:
    return str(row.get("attempt_kind", "primary")).strip().lower() == "primary"


def is_e2_or_e3(row: dict[str, Any]) -> bool:
    return str(row.get("experiment_id", "")).upper() in {"E2", "E3"}


def has_failure(row: dict[str, Any]) -> bool:
    return any(bool(row.get(name)) for name in ("schema_failure", "repetition_loop", "state_contradiction"))


def max_tokens_for(row: dict[str, Any], default_max_tokens: int) -> int:
    value = row.get("max_tokens")
    if isinstance(value, int) and value > 0:
        return value
    return default_max_tokens


def is_near_cap(row: dict[str, Any], threshold: float, default_max_tokens: int) -> bool:
    tokens_out = row.get("tokens_out")
    if not isinstance(tokens_out, int):
        return False
    max_tokens = max_tokens_for(row, default_max_tokens)
    return tokens_out >= int(threshold * max_tokens)


def is_json_extractable(response_text: str) -> bool:
    try:
        json.loads(response_text)
    except json.JSONDecodeError:
        return False
    return True


def tally_rows(rows: list[dict[str, Any]], threshold: float, default_max_tokens: int) -> Counter[str]:
    tally: Counter[str] = Counter()
    for row in rows:
        tally["rows"] += 1
        if not has_failure(row):
            continue

        tally["failed"] += 1
        if is_near_cap(row, threshold, default_max_tokens):
            tally["near_cap"] += 1

        schema_failure = bool(row.get("schema_failure"))
        repetition_loop = bool(row.get("repetition_loop"))
        state_contradiction = bool(row.get("state_contradiction"))
        response_text = str(row.get("response", ""))

        if schema_failure:
            if is_json_extractable(response_text):
                tally["schema_extractable"] += 1
            else:
                tally["schema_non_extractable"] += 1

        if schema_failure and repetition_loop:
            tally["schema_plus_rep"] += 1
        elif schema_failure:
            tally["schema_only"] += 1
        elif repetition_loop and not state_contradiction:
            tally["repetition_only"] += 1
        elif state_contradiction and not schema_failure and not repetition_loop:
            tally["state_only"] += 1
        else:
            tally["other_failure"] += 1

    return tally


def with_rates(row: dict[str, Any]) -> dict[str, Any]:
    failed = int(row.get("failed", 0))
    rows = int(row.get("rows", 0))
    out = dict(row)
    out["fail_rate"] = round((failed / rows) if rows else 0.0, 6)
    for key in (
        "near_cap",
        "schema_extractable",
        "schema_non_extractable",
        "schema_only",
        "schema_plus_rep",
        "repetition_only",
        "state_only",
        "other_failure",
    ):
        out[key] = int(row.get(key, 0))
        out[f"{key}_share_of_failed"] = round((out[key] / failed) if failed else 0.0, 6)
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    rows = read_jsonl(Path(args.input))
    filtered = [row for row in rows if is_primary(row) and is_e2_or_e3(row)]

    by_model: dict[str, list[dict[str, Any]]] = {}
    for row in filtered:
        by_model.setdefault(str(row.get("model", "unknown")), []).append(row)

    fieldnames = [
        "model",
        "rows",
        "failed",
        "fail_rate",
        "near_cap",
        "near_cap_share_of_failed",
        "schema_extractable",
        "schema_extractable_share_of_failed",
        "schema_non_extractable",
        "schema_non_extractable_share_of_failed",
        "schema_only",
        "schema_only_share_of_failed",
        "schema_plus_rep",
        "schema_plus_rep_share_of_failed",
        "repetition_only",
        "repetition_only_share_of_failed",
        "state_only",
        "state_only_share_of_failed",
        "other_failure",
        "other_failure_share_of_failed",
    ]

    by_model_rows: list[dict[str, Any]] = []
    for model in sorted(by_model):
        tally = tally_rows(by_model[model], args.near_cap_threshold, args.default_max_tokens)
        row = with_rates({"model": model, **tally})
        by_model_rows.append(row)

    overall_tally = tally_rows(filtered, args.near_cap_threshold, args.default_max_tokens)
    overall_row = with_rates({"model": "overall", **overall_tally})

    write_csv(Path(args.output_by_model), by_model_rows, fieldnames)
    write_csv(Path(args.output_overall), [overall_row], fieldnames)


if __name__ == "__main__":
    main()
