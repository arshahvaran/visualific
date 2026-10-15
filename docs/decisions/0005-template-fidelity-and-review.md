# 0005. Templates improve on the originals, and the author approves each one

- Status: accepted. The author set this policy.
- Date: 2026-10-15

## Context

Each of the first templates starts from a figure in a paper the author wrote or co-authored; a contributed template starts from a published figure the contributor names. Some choices in those figures are worth keeping, such as direct labels, restrained palettes and grey reference series. Others predate the house style in [0002](0002-house-style.md) and the colour rules in [0003](0003-default-palette.md).

## Decision

Templates follow 0002, 0003 and the design rules in the README, and improve on the originals where they conflict. Each template goes through these steps:

1. **Specification.** A table lists what is kept from the original, what changes and why. The author approves it before any code is written.
2. **Measured checks.** The rendered figure must pass automated checks: saved width, minimum text size and line width at print size, embedded fonts, approved colours, and no clipped or overlapping text.
3. **Review panel.** AI reviewer agents, one per angle, compare the new figure with the original at the same physical size. The angles are typography; spacing and alignment; colour and encoding; fidelity to the original's design; and clutter. One blocking defect sends the figure back for a fix.
4. **Approval.** The author approves a side-by-side comparison. This is the human review of the finished figure; the author has already approved the specification in step 1. The approved figure then becomes a test reference: structural checks run on every platform from v0.1, and from v0.2 an image comparison with a tolerance runs on one pinned Linux job with Liberation Serif, so a later change that alters the figure fails a test.

A `legacy` option reproduces an original's look where that is needed, for example to match figures already published in a paper.

## Consequences

- Templates take longer to add, and each one has a record of what was decided.
- Contributed templates go through the same steps.
