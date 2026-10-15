# 0006. Scope and release plan

- Status: accepted. The author set the scope, made the repository public from the start and decided that study-area maps are rebuilt in Python. The author left the v0.1 feature list and the contents and order of later releases to the assistant, which chose them.
- Date: 2026-10-15

## Context

Visualific is a side project with one maintainer. The figures it draws on cover model evaluation, distributions, matrices, time series, sets and networks, and maps. Many single chart types already exist in other packages, so Visualific's contribution is a set of templates that share the house style, the millimetre sizing and `vf.check`.

## Decision

- Visualific is a general figure library for engineering and environmental research, not limited to one niche.
- Releases stay small, and features are added once the earlier ones are solid.
- **v0.1:**
  - house style, millimetre widths, palettes and the save helper;
  - a basic `vf.check` with five measurements;
  - a one-line style for SciencePlots users, using the `vf.science_safe` colours;
  - the synthetic datasets;
  - six templates: observed versus predicted, Taylor diagram, error ECDF, raincloud plot, correlation heatmap and a stacked time series;
  - the gallery notebook.
- **v0.2:**
  - an UpSet plot that fits in one panel, ridgeline, pair matrix, split-cell heatmap and SHAP force plot;
  - more journal profiles (Springer, ASCE, IWA, Copernicus);
  - a guide that tells AI coding assistants to call Visualific's templates;
  - a documentation site.
- **v0.3:** maps (Peirce quincuncial point maps, and study-area maps rebuilt in Python with synthetic terrain and land cover), chord and alluvial diagrams, and causal graphs.
- The repository is public from the first commit.

## Consequences

- Early releases cover a few figure types thoroughly.
- Map support adds heavier optional dependencies, so it comes last and installs as an extra.
