from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


def parse_int_list(text: str) -> list[int]:
    values = sorted({int(part.strip()) for part in text.split(",") if part.strip()})
    if not values or any(value <= 0 for value in values):
        raise ValueError("expected comma-separated positive integers")
    return values


def subsample_indices(n_cells: int, count: int, seed: int) -> np.ndarray:
    if count > n_cells:
        raise ValueError(
            f"requested {count} cells but prediction contains only {n_cells}"
        )
    if count == n_cells:
        return np.arange(n_cells)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n_cells, size=count, replace=False))


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def summarize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[int(record["cells"])].append(record)

    output: list[dict[str, Any]] = []
    for cells in sorted(grouped):
        rows = grouped[cells]
        metric_names = sorted(
            {
                name
                for row in rows
                for name in row.get("metrics", {})
                if not str(name).startswith("_")
            }
        )
        summary: dict[str, Any] = {"cells": cells, "n_seeds": len(rows)}
        for metric in metric_names:
            values: list[float] = []
            for row in rows:
                numeric = _numeric(row.get("metrics", {}).get(metric))
                if numeric is not None:
                    values.append(numeric)
            if not values:
                continue
            summary[f"{metric}_mean"] = statistics.fmean(values)
            summary[f"{metric}_sd"] = (
                statistics.pstdev(values) if len(values) > 1 else 0.0
            )
        output.append(summary)
    return output


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = sorted(
        {key for row in rows for key in row},
        key=lambda key: (key not in {"cells", "n_seeds"}, key),
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
