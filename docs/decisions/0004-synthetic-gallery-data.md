# 0004. Synthetic gallery data: one archive of four tidy tables

- Status: accepted. The author chose one archive of four tables; the assistant designed the generator.
- Date: 2026-10-15

## Context

Every template needs example data, and the gallery must run anywhere without the original study data. The templates need four different shapes of data: daily records for monitored lakes, model predictions in long form, a point inventory with coordinates and covariates, and a yearly panel. Forcing these into one CSV would leave about 90 mostly empty columns.

## Decision

- The gallery data ship as one archive, `visualific_synthetic.zip`, containing four tidy CSV tables: daily lake records (the main table), lake predictions, a lake inventory and an annual lake panel.
- All values come from a documented, seeded generator describing a fictional observatory of twelve monitored lakes within a larger fictional lake inventory. Lake names, identifiers and file names mark the data as synthetic, and no place or site in the data refers to a real study.
- The generator is the specification. A frozen snapshot of its output is what the package ships, because NumPy does not guarantee identical random streams across versions.
- `vf.datasets.load_*()` functions read the tables and return pandas DataFrames.

## Consequences

- Users get one file and can still open each table in a spreadsheet.
- Tests regenerate the data with the NumPy version that produced the snapshot and compare within a tolerance. With other NumPy versions they check the schema and summary statistics only.
- A template that needs a new kind of data extends the generator and the snapshot together.
