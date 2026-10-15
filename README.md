# Visualific

[![tests](https://github.com/arshahvaran/visualific/actions/workflows/tests.yml/badge.svg)](https://github.com/arshahvaran/visualific/actions/workflows/tests.yml)
[![licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](https://github.com/arshahvaran/visualific/blob/main/LICENSE)

Publication figures for engineering and environmental research, drawn at their final size in one house style.

> **Status: early development.** There is no release on PyPI yet. The plan for the first release is below, and the design decisions behind it are recorded in [`docs/decisions`](https://github.com/arshahvaran/visualific/tree/main/docs/decisions).

## The idea

Figure code is often written at screen size, and the figure is shrunk to fit a journal column afterwards. After shrinking, tick labels can print at 4 or 5 pt, lines thin out to hairlines, and colours that looked distinct on screen can merge for colour-blind readers. Visualific is designed to draw the figure at the printed width from the start: you choose the column width, and type sizes and line weights are set for that width.

The first figure templates come from published papers in hydrology, limnology and remote sensing that the author wrote or co-authored. Each one will be rebuilt on synthetic data and reviewed against the original before release.

## Installation

Nothing is released yet. To try the current state of the code:

```bash
pip install git+https://github.com/arshahvaran/visualific
```

From v0.1 this becomes `pip install visualific`.

## Planned for v0.1

- `vf.use()` sets the house style: Times New Roman (falling back to Liberation Serif, then STIXGeneral), 8, 9 and 10 pt type at print size, and line weights given in points.
- Journal widths in millimetres: Elsevier (90, 140 and 190 mm) and Nature (89 and 183 mm). The Nature preset sets the width only; Nature asks for 5 to 7 pt Arial or Helvetica, which needs its own profile.
- `vf.save()` writes a PDF with embedded fonts, which is the file to submit, and a 600 dpi PNG for previews, both at the declared width to within 0.5 mm. Elsevier asks for 1000 dpi when line art is sent as a bitmap, so TIFF output sets its resolution by content type.
- Palettes drawn from the [Rang](https://github.com/mohsennasab/Rang) colours and checked under simulated colour vision deficiency. For people moving over from SciencePlots, `vf.use("science-like")` uses a version of its colours adjusted for colour vision deficiency.
- `vf.check(fig)` measures a finished figure: the smallest text and thinnest line at print size, the saved width, text that falls off the canvas, and whether the plotted series can still be told apart under simulated protanopia, deuteranopia and tritanopia, and, for figures meant for greyscale printing, in greyscale.
- Six templates: observed versus predicted, Taylor diagram, error ECDF, raincloud plot, correlation heatmap and a stacked time series.
- A gallery notebook that runs every template on synthetic data, with all style settings in its first cell.

Later releases are planned to add an UpSet plot that fits in a single panel, ridgeline and pair plots, SHAP force plots, more journal profiles, and maps, including the Peirce quincuncial projection and study-area maps.

## Design rules

1. One message per figure. Small multiples of one chart type work well; avoid a different chart type in each panel.
2. Draw at the final size, never larger and then shrunk.
3. Each colour has one job and one meaning across all the figures of a paper. Reference data are grey.
4. Label lines and groups directly where possible, and use at most one legend.
5. Every figure can be rebuilt from code, with no editing by hand afterwards.

`vf.check` will turn the measurable parts of these rules into checks.

## Related work and credits

- [Rang](https://github.com/mohsennasab/Rang) by Mohsen Tahmasebi Nasab supplies the palette colours. Its palette values are CC0 and will be copied into Visualific with credit.
- [SciencePlots](https://github.com/garrettj403/SciencePlots) by John D. Garrett provides one-line matplotlib styles for papers.
- [BeautifulFigures](https://github.com/AndreyChurkin/BeautifulFigures) by Andrey Churkin presents figure design as a sequence of small, visible improvements.
- [journalfig](https://github.com/Atilaac/journalfig) offers sourced journal themes for twelve publishers and a compliance checker (`jf.check`). [UltraPlot](https://github.com/Ultraplot/UltraPlot) handles multi-panel layout, and [modelskill](https://github.com/DHI/modelskill) makes model-skill plots.

## AI assistance

Visualific is developed with an AI coding assistant (Claude Code). The author set the project's direction and its core style (typeface, type scale and default palette) and approves every template before release. The assistant chose the v0.1 features and derived the other style values and the design rules from the author's published figures. [`AI_USAGE.md`](https://github.com/arshahvaran/visualific/blob/main/AI_USAGE.md) records what the assistant did.

## Licence

The code is MIT licensed. Palette values taken from Rang are CC0.
