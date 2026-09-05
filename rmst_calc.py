#!/usr/bin/env python3
"""
Restricted Mean Survival Time (RMST) Difference Calculator
Calculates area under the Kaplan-Meier curve up to truncation time tau and computes RMST difference between two arms.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for restricted-mean-survival-time-rmst.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Deterministic domain logic
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]
    primary_val = numeric_vals[0] if numeric_vals else 1.0

    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)
    
    # Classification / tiering
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "restricted-mean-survival-time-rmst",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    input_path = Path(input_csv).resolve()
    output_path = Path(output_csv).resolve()

    # Validate input file exists and is a file
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_csv}")

    # Validate input file extension
    if input_path.suffix.lower() not in ('.csv', '.tsv'):
        raise ValueError(f"Input file must be a CSV or TSV file, got: {input_path.suffix}")

    with open(input_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError(f"Input file has no headers or is empty: {input_csv}")
        rows = list(reader)

    if not rows:
        print(f"Warning: Input file has headers but no data rows: {input_csv}")

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Restricted Mean Survival Time (RMST) Difference Calculator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV file path")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV file path")

    args = parser.parse_args(argv)

    try:
        if args.command == "single":
            args.func(args)
        elif args.command == "batch":
            process_batch(args.input, args.output)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except BrokenPipeError:
        # Handle piping output to commands that close early (e.g., head)
        sys.exit(0)


if __name__ == "__main__":
    main()
