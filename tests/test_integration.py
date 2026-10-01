from __future__ import annotations

import subprocess
import sys

import anndata as ad
import numpy as np
import pandas as pd


def _write(path, expression, genes, celltypes=None):
    obs = pd.DataFrame(index=[f"cell_{i}" for i in range(len(expression))])
    if celltypes is not None:
        obs["celltype"] = celltypes
    data = ad.AnnData(
        X=np.asarray(expression, dtype=np.float32),
        obs=obs,
        var=pd.DataFrame(index=genes),
    )
    data.write_h5ad(path)


def test_real_veckit_t1_end_to_end(tmp_path):
    rng = np.random.default_rng(4)
    n_cells, n_genes = 90, 32
    genes = [f"g{i}" for i in range(n_genes)]
    labels = np.array(["A"] * 45 + ["B"] * 45)

    reference = np.log1p(
        rng.poisson(3.0, size=(n_cells, n_genes))
    ).astype(np.float32)
    target = reference.copy()
    target[:, :8] += 0.45
    target[:, 8:16] = np.maximum(target[:, 8:16] - 0.35, 0)
    prediction = np.maximum(
        target + rng.normal(0, 0.08, target.shape),
        0,
    )

    pred_path = tmp_path / "pred.h5ad"
    target_path = tmp_path / "target.h5ad"
    ref_path = tmp_path / "ref.h5ad"
    out_dir = tmp_path / "out"

    _write(pred_path, prediction, genes)
    _write(target_path, target, genes, labels)
    _write(ref_path, reference, genes, labels)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_samplecheck.cli",
            str(pred_path),
            "--task",
            "T1",
            "--target",
            str(target_path),
            "--reference",
            str(ref_path),
            "--counts",
            "40,70",
            "--seeds",
            "1,2",
            "--out",
            str(out_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (out_dir / "records.json").exists()
    assert (out_dir / "summary.csv").exists()
    report = (out_dir / "report.md").read_text()
    assert "| 40 | 2 |" in report
    assert "| 70 | 2 |" in report
