# Visualific

[![tests](https://github.com/arshahvaran/visualific/actions/workflows/tests.yml/badge.svg)](https://github.com/arshahvaran/visualific/actions/workflows/tests.yml)
[![licence: MIT AND OFL-1.1 AND CC0-1.0](https://img.shields.io/badge/licence-MIT%20AND%20OFL--1.1%20AND%20CC0--1.0-blue.svg)](https://github.com/arshahvaran/visualific/blob/main/LICENSES/README.md)

Publication figures for engineering and environmental research, drawn at their final size in one house style.

> **Status: early development.** There is no release on PyPI yet. The house style, millimetre widths, palettes, save helper and figure check are in the code; so is the synthetic example data. The figure templates and the gallery notebook are still to come. The design decisions are recorded in [`docs/decisions`](https://github.com/arshahvaran/visualific/tree/main/docs/decisions).

## The idea

Figure code is often written at screen size, and the figure is shrunk to fit a journal column afterwards. After shrinking, tick labels can print at 4 or 5 pt, lines thin out to hairlines, and colours that looked distinct on screen can merge for colour-blind readers. Visualific is designed to draw the figure at the printed width from the start: you choose the column width, and type sizes and line weights are set for that width.

The first figure templates come from published papers in hydrology, limnology and remote sensing that the author wrote or co-authored. Each one will be rebuilt on synthetic data and reviewed against the original before release.

## Installation

Nothing is released yet. To try the current state of the code:

```bash
pip install git+https://github.com/arshahvaran/visualific
```

From v0.1 this becomes `pip install visualific`.

## Quick start

```python
import matplotlib.pyplot as plt
import numpy as np
import visualific as vf

vf.use()

t = np.arange(120)
fig, ax = plt.subplots(figsize=vf.figsize("elsevier-single", 60))  # 90 x 60 mm
ax.plot(t, 5 + np.sin(t / 10), color=vf.OBSERVED_GREY, label="Observed")
models = {"Model A": 0.3, "Model B": -0.4}
for (name, shift), style in zip(models.items(), vf.qual.styles(len(models))):
    ax.plot(t, 5 + np.sin(t / 10 + shift), label=name, **style)
ax.set(xlabel="Time (d)", ylabel=r"Discharge (m$^3$ s$^{-1}$)")
ax.legend()

print(vf.check(fig, width="elsevier-single"))
vf.save(fig, "fig1", width="elsevier-single")  # writes fig1.pdf and fig1.png
```

## What works now

- `vf.use()` and the `vf.style()` context set the house style: Times New Roman, falling back to the bundled Liberation Serif and then STIXGeneral; 8, 9 and 10 pt type at print size, or 7, 8 and 9 pt with `compact=True`; and line weights given in points. Mathematics is set in STIX, so no LaTeX installation is needed. Sub- and superscripts are kept at 6 pt or larger for the rest of the session once `vf.use`, `vf.style`, `vf.save` or `vf.check` has run; a script inside a script can still be smaller, and `vf.check` reports it.
- `vf.figsize()` takes a width in millimetres or a journal preset: Elsevier (90, 140 and 190 mm) and Nature (89 and 183 mm), each with its source page and the date it was read. The Nature presets set the width only; Nature asks for 5 to 7 pt Arial or Helvetica, which needs its own profile.
- `vf.save()` writes a PDF with TrueType fonts, which is the file to submit, and a 600 dpi PNG for previews, then measures each file to confirm that it is the declared width to within 0.5 mm. TIFF output sets its resolution by content type, as Elsevier asks: 1000 dpi for line art, 500 dpi for combination art and 300 dpi for photographs. JPEG is refused.
- Palettes from the [Rang](https://github.com/mohsennasab/Rang) colours: `vf.qual` (categorical, checked under simulated colour vision deficiency), `vf.termeh` and `vf.rostan` (sequential, light to dark) and `vf.mina_div` (diverging, light at the centre). `vf.qual.styles(n)` gives every series its own marker from the fifth category on. Observed or reference data use one grey, `vf.OBSERVED_GREY` (#808080).
- `vf.use("science-like")` is for people moving over from SciencePlots: ticks inside on all four sides, as SciencePlots draws them, with `vf.science_safe`, a version of the SciencePlots colours adjusted for colour vision deficiency. The original SciencePlots colours are in `vf.legacy`, for reproducing published figures only.
- `vf.datasets` loads the synthetic example data: daily records for twelve fictional lakes, model predictions, a lake inventory and a yearly panel, shipped as one archive of four CSV tables (`vf.datasets.load_lakes_daily()` and so on; `vf.datasets.describe()` gives units and descriptions). Every value is generated from a seed, and no place in the data refers to a real study.
- `vf.check(fig)` measures a finished figure: the smallest text (sub- and superscripts included) and the thinnest line at print size, the saved width, and any text that runs past the figure edge. It also measures how far apart the plotted colours are, as a CIEDE2000 colour difference (shown as dE00), under normal vision and simulated protanopia, deuteranopia and tritanopia, and in greyscale on request.

## Still to come in v0.1

- Six templates: observed versus predicted, Taylor diagram, error ECDF, raincloud plot, correlation heatmap and a stacked time series.
- A gallery notebook that runs every template on the synthetic data, with all style settings in its first cell.

Later releases are planned to add an UpSet plot that fits in a single panel, ridgeline and pair plots, SHAP force plots, more journal profiles, and maps, including the Peirce quincuncial projection and study-area maps.

## Design rules

1. One message per figure. Small multiples of one chart type work well; avoid a different chart type in each panel.
2. Draw at the final size, never larger and then shrunk.
3. Each colour has one job and one meaning across all the figures of a paper. Reference data are grey.
4. Label lines and groups directly where possible, and use at most one legend.
5. Every figure can be rebuilt from code, with no editing by hand afterwards.

`vf.check` already measures rule 2 (text and line sizes at print size, the saved width) and whether the plotted colours can be told apart. More of the rules will become checks.

## Related work and credits

- [Rang](https://github.com/mohsennasab/Rang) by Mohsen Tahmasebi Nasab supplies the palette colours. Its palette values are CC0 and are copied into Visualific unchanged, with credit.
- [SciencePlots](https://github.com/garrettj403/SciencePlots) by John D. Garrett provides one-line matplotlib styles for papers.
- [BeautifulFigures](https://github.com/AndreyChurkin/BeautifulFigures) by Andrey Churkin presents figure design as a sequence of small, visible improvements.
- [journalfig](https://github.com/Atilaac/journalfig) offers sourced journal themes for twelve publishers and a compliance checker (`jf.check`). [UltraPlot](https://github.com/Ultraplot/UltraPlot) handles multi-panel layout, and [modelskill](https://github.com/DHI/modelskill) makes model-skill plots.

## AI assistance

Visualific is developed with an AI coding assistant (Claude Code). The author set the project's direction and its core style (typeface, type scale and default palette) and approves every template before release. The assistant chose the v0.1 features, derived the other style values and the design rules from the author's published figures, and writes the code and tests. The author has not yet reviewed the code. [`AI_USAGE.md`](https://github.com/arshahvaran/visualific/blob/main/AI_USAGE.md) records what the assistant did.

## Licence

The code is MIT licensed. Visualific also includes the Liberation Serif font (version 2.1.5, unmodified) under the SIL Open Font License 1.1, and palette values from Rang under CC0 1.0, so the package licence is `MIT AND OFL-1.1 AND CC0-1.0`. [`LICENSES`](https://github.com/arshahvaran/visualific/tree/main/LICENSES) says which files each licence covers.
