from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .core import parse_int_list, subsample_indices, summarize, write_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure VEC local-score sensitivity to prediction cell count."
    )
    parser.add_argument("prediction", type=Path)
    parser.add_argument("--task", required=True, choices=["T1", "T2", "T3"])
    parser.add_argument("--setting", default="heart", choices=["heart", "embryo"])
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--wt", type=Path)
    parser.add_argument("--counts", default="1000,1500,2000,3000,5000")
    parser.add_argument("--seeds", default="0,1,2,3,4")
    parser.add_argument("--out", type=Path, default=Path("samplecheck_out"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    import anndata as ad
    from veckit import score

    counts = parse_int_list(args.counts)
    seeds = parse_int_list(args.seeds)
    prediction = ad.read_h5ad(args.prediction)

    if max(counts) > prediction.n_obs:
        raise SystemExit(
            f"largest requested count ({max(counts)}) exceeds prediction cells "
            f"({prediction.n_obs})"
        )
    if args.task in {"T1", "T2"} and args.reference is None:
        raise SystemExit("--reference is required for T1/T2")
    if args.task == "T3" and args.wt is None:
        raise SystemExit("--wt is required for T3")

    args.out.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    with tempfile.TemporaryDirectory() as temporary:
        temp_dir = Path(temporary)
        for count in counts:
            for seed in seeds:
                indices = subsample_indices(prediction.n_obs, count, seed)
                temp_path = temp_dir / f"n{count}_seed{seed}.h5ad"
                prediction[indices].copy().write_h5ad(temp_path)

                kwargs = {
                    "task": args.task,
                    "input": temp_path,
                    "target": args.target,
                    "seed": seed,
                }
                if args.task in {"T1", "T2"}:
                    kwargs["reference"] = args.reference
                if args.task == "T2":
                    kwargs["setting"] = args.setting
                if args.task == "T3":
                    kwargs["wt"] = args.wt

                result = score(**kwargs)
                records.append(
                    {"cells": count, "seed": seed, "metrics": result["metrics"]}
                )

    summaries = summarize(records)
    (args.out / "records.json").write_text(
        json.dumps(records, indent=2, default=float) + "\n",
        encoding="utf-8",
    )
    write_csv(summaries, args.out / "summary.csv")

    lines = [
        "# VEC SampleCheck",
        "",
        "| cells | seeds | maximum metric SD |",
        "|---:|---:|---:|",
    ]
    for row in summaries:
        standard_deviations = [
            float(value)
            for key, value in row.items()
            if key.endswith("_sd")
        ]
        max_sd = max(standard_deviations, default=0.0)
        lines.append(f"| {row['cells']} | {row['n_seeds']} | {max_sd:.6g} |")
    lines.extend(
        [
            "",
            "> Local pseudo-split sensitivity only; not a hidden-test estimate.",
            "",
        ]
    )
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
