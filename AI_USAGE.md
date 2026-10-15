# AI usage log

Visualific is built with the help of an AI coding assistant. This log records where it was used, so that readers, reviewers and journals can see who did what. Journals such as JOSS and SoftwareX ask authors to disclose AI assistance, and a record kept as the work happens is more reliable than one reconstructed later.

**Tool:** Claude Code 2.1.299 (Anthropic), running the Claude Opus 5.5 model (`claude-opus-5-5`). Claude Code also runs separate AI reviewer agents that audit drafts and figures.

**Division of work:**

- The author chose the positioning, the typeface, the type scale (8, 9 and 10 pt), the Rang colours and the default palette `vf.qual`, the gallery data format, and the rule that templates improve on the originals and need the author's approval.
- The assistant derived the other house-style values (line weights, export settings), the five design rules in the README and `vf.science_safe` from the author's published figures and its colour analysis. Each record in [`docs/decisions`](docs/decisions) says who decided.
- The author left the v0.1 feature list and the contents of later releases to the assistant, which chose them ([0006](docs/decisions/0006-scope-and-release-plan.md)).
- The assistant drafts code, tests and documentation, runs audits with AI reviewer agents, and prepares side-by-side comparisons of figures.
- The author approves each template against the original figure before release.

| Date | Area | What the assistant did | Human review |
|---|---|---|---|
| 2026-10-15 | Research | Reviewed the scripts and outputs behind the author's published figures to derive the house style and the design rules, drafted the synthetic-data generator described in [0004](docs/decisions/0004-synthetic-gallery-data.md), surveyed related packages, compared colour palettes under simulated colour vision deficiency, and derived the adjusted SciencePlots colours | The author chose the positioning, type scale, default palette and data format from the options presented. The author left the v0.1 feature list to the assistant. |
| 2026-10-15 | Repository | Drafted the project skeleton, README and decision records, then had AI reviewer agents audit them for privacy, packaging, prose and numerical accuracy in two rounds before publication | The author approved publishing the repository and chose the public commit identity |
