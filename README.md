# VEC SampleCheck

The official VEC documentation says cell count is a **sample size, not a scored biological quantity**, and that the heaviest metrics subsample roughly 1,500-2,000 cells. `vec-samplecheck` lets a team verify that statement on its own model output before choosing how many generated cells to export.

It deterministically downsamples one prediction to several candidate sizes, scores each subsample with `veckit` across one or more seeds, and reports metric mean/SD by cell count.

## Example

```bash
vec-samplecheck prediction.h5ad \
  --task T2 --setting heart \
  --target pseudo_target.h5ad \
  --reference preceding_stage.h5ad \
  --counts 1000,1500,2000,3000,5000 \
  --seeds 0,1,2,3,4 \
  --out results
```

Outputs:

- `records.json` — every count × seed metric panel;
- `summary.csv` — mean/SD per metric at each cell count;
- `report.md` — compact stability table.

For T3 use `--wt` instead of `--reference`.

## Interpretation

If 2,000 and 5,000 cells are statistically indistinguishable on the same pseudo split, generating/uploading the larger file probably buys little for that model. This is **not** a hidden-test estimate; it only measures sensitivity of the public local scoring procedure on data you already have.
