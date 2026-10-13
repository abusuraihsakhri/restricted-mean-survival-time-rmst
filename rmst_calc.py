#!/usr/bin/env python3
"""Restricted mean survival time from right-censored individual-level observations.

Kaplan–Meier estimator with event-before-censor tie handling. This is a
descriptive, unadjusted estimator; no hypothesis tests or confidence intervals.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence


def _number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _event(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if str(value).strip() not in ("0", "1", "0.0", "1.0"):
        raise ValueError("event must be 0 (censored) or 1 (event)")
    return int(float(value))


def _estimate(records: list[tuple[float, int]], tau: float) -> dict[str, Any]:
    """Integrate the right-continuous KM step curve on [0, tau]."""
    counts: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    for time, event in records:
        counts[time][0 if event else 1] += 1
    at_risk = len(records)
    survival = 1.0
    previous = 0.0
    area = 0.0
    steps = [{"time": 0.0, "survival": 1.0}]
    for time, (events, censored) in sorted(counts.items()):
        if time > tau:
            break
        area += (time - previous) * survival
        survival *= 1.0 - events / at_risk
        at_risk -= events + censored
        previous = time
        # Include censor-only times to disclose the extent of observation.
        steps.append({"time": time, "survival": max(0.0, survival)})
    area += (tau - previous) * survival
    area = min(tau, max(0.0, area))  # guard against floating-point roundoff
    return {
        "n": len(records),
        "events": sum(event for _, event in records),
        "censored": sum(1 - event for _, event in records),
        "rmst": area,
        "rmtl": tau - area,
        "curve": steps,
    }


def calculate_metrics(rows: Sequence[Mapping[str, Any]], tau: float) -> dict[str, Any]:
    """Compute KM RMST and optionally an unadjusted two-group contrast.

    Each row has time >= 0, event in {0, 1}, and optional group (default 'All').
    Units of RMST equal those of the input time variable. Tau must be positive
    and no greater than the largest observed time within each group.
    """
    tau = _number(tau, "tau")
    if tau <= 0:
        raise ValueError("tau must be greater than zero")
    grouped: dict[str, list[tuple[float, int]]] = {}
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise ValueError(f"row {index} must be a mapping")
        time = _number(row.get("time"), f"row {index}: time")
        if time < 0:
            raise ValueError(f"row {index}: time cannot be negative")
        event = _event(row.get("event"))
        group = str(row.get("group", "All")).strip()
        if not group:
            raise ValueError(f"row {index}: group must not be empty")
        grouped.setdefault(group, []).append((time, event))
    if not grouped:
        raise ValueError("at least one observation is required")
    if len(grouped) > 2:
        raise ValueError("at most two groups are supported")
    for group, observations in grouped.items():
        if tau > max(time for time, _ in observations):
            raise ValueError(
                f"tau ({tau:g}) exceeds maximum observed time in group {group!r}; "
                "KM extrapolation is not supported"
            )
    results = {group: _estimate(observations, tau) for group, observations in sorted(grouped.items())}
    output: dict[str, Any] = {"tau": tau, "groups": results, "contrast": None}
    if len(results) == 2:
        first, second = list(results)
        a, b = results[first]["rmst"], results[second]["rmst"]
        output["contrast"] = {
            "reference": first,
            "comparison": second,
            "difference": b - a,
            "ratio": b / a if a > 0 else None,
            "direction": f"{second} minus {first}",
        }
    return output


def read_observations(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.suffix.lower() not in (".csv", ".tsv"):
        raise ValueError("Input file must be a CSV or TSV file")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t" if path.suffix.lower() == ".tsv" else ",")
        columns = reader.fieldnames or []
        if not {"time", "event"}.issubset(columns):
            raise ValueError("Input requires 'time' and 'event' columns")
        if len(columns) != len(set(columns)):
            raise ValueError("Duplicate CSV column names")
        rows = []
        for index, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Row {index} has too many fields")
            if not any(str(v or "").strip() for v in row.values()):
                continue
            rows.append(row)
    return rows


def process_batch(input_csv: str, output_csv: str, tau: float) -> dict[str, Any]:
    """Analyze one patient-level dataset and export a per-group summary CSV."""
    if Path(input_csv).resolve() == Path(output_csv).resolve():
        raise ValueError("Input and output paths must differ")
    result = calculate_metrics(read_observations(input_csv), tau)
    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["group", "tau", "n", "events", "censored", "rmst", "rmtl"])
        writer.writeheader()
        for group, values in result["groups"].items():
            writer.writerow({key: value for key, value in {
                "group": group, "tau": result["tau"], **values
            }.items() if key in writer.fieldnames})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unadjusted Kaplan–Meier restricted mean survival time")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Analyze inline observations")
    single.add_argument("--times", nargs="+", type=float, required=True)
    single.add_argument("--events", nargs="+", required=True)
    single.add_argument("--groups", nargs="*", help="Optional group label per observation")
    single.add_argument("--tau", type=float, required=True)
    batch = commands.add_parser("batch", help="Analyze a patient-level CSV/TSV file")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    batch.add_argument("--tau", type=float, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            if len(args.times) != len(args.events) or (
                args.groups is not None and len(args.groups) != len(args.times)
            ):
                raise ValueError("--times, --events and --groups (if provided) must have equal length")
            rows = [
                {"time": time, "event": event, "group": args.groups[i] if args.groups else "All"}
                for i, (time, event) in enumerate(zip(args.times, args.events))
            ]
            result = calculate_metrics(rows, args.tau)
        else:
            result = process_batch(args.input, args.output, args.tau)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
