# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Project skeleton: packaging, licence, continuous integration, contribution guide, citation file, AI usage log and design decision records.
- House style ([0002](docs/decisions/0002-house-style.md)): `vf.use()`, the `vf.style()` context and `vf.rc_params()`. Times New Roman, then the bundled Liberation Serif, then STIXGeneral; 8, 9 and 10 pt type, or 7, 8 and 9 pt with `compact=True`; line weights in points; constrained layout; mathematics in STIX without LaTeX. Mathtext sub- and superscripts are kept at 6 pt or larger (a script inside a script can still be smaller; `vf.check` reports it).
- `vf.use("science-like")` for SciencePlots users: inward ticks on all four sides with the `vf.science_safe` colours.
- Widths in millimetres (`vf.figsize`, `vf.WIDTHS`): Elsevier 90, 140 and 190 mm and Nature 89 and 183 mm (widths only), each with its source page and access date.
- Palettes ([0003](docs/decisions/0003-default-palette.md)): `vf.qual`, `vf.science_safe`, sequential `vf.termeh` and `vf.rostan`, diverging `vf.mina_div` with its light colour at the centre, and `vf.legacy` sets that warn when accessed. `Palette.styles(n)` adds markers from the fifth category on. Tests pin the measured colour separations.
- `vf.save()`: PDF with TrueType (Type 42) fonts and a 600 dpi PNG, each measured to be the declared width within 0.5 mm; TIFF (RGB, no alpha channel) at 1000, 500 or 300 dpi by content type; SVG with text as paths; JPEG and other formats refused.
- `vf.check()`: smallest text including scripts, thinnest line, saved width, text outside the figure, and colour separation of the plotted series under simulated colour vision deficiency (and greyscale on request).
- Bundled Liberation Serif 2.1.5 (SIL Open Font License 1.1) and the Rang 0.3.0 palette values (CC0 1.0), both unmodified. The package licence is `MIT AND OFL-1.1 AND CC0-1.0`; see `LICENSES/`.
- Pillow and cycler as declared dependencies (matplotlib already requires them).
- A continuous-integration job that installs the lowest supported dependency versions (cycler 0.10, matplotlib 3.9, numpy 1.26, pandas 2.1, pillow 9.3, with `pyparsing<3.3`) on Python 3.11 and runs the tests, so the floors in `pyproject.toml` stay true.

[Unreleased]: https://github.com/arshahvaran/visualific/commits/main
