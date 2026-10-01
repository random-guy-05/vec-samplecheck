# Community Contribution submission text

## Title
VEC SampleCheck — cell-count sensitivity tester for local scoring

## Description
SampleCheck answers a practical question the official docs raise but every team otherwise has to test manually: how many generated cells are enough for *my* prediction? It deterministically downsamples one H5AD to several cell counts, runs the official `veckit` metric panel over multiple scorer seeds, and reports mean/SD of every metric by count. The tool is explicitly a pseudo-split sensitivity analysis, not a hidden-score predictor. It helps teams avoid unnecessary generation, file size and scoring cost when metrics have already stabilized near the scorer's own 1,500-2,000-cell subsampling scale.
