# 0003. Default categorical palette and colour rules

- Status: accepted. The author chose the Rang colours and `vf.qual`; the assistant set the measurement method and thresholds and derived `vf.science_safe`.
- Date: 2026-10-15

## Context

Colour must separate categories for every reader, including about 1 in 12 men of Northern European ancestry (Birch 2012) who have a red-green colour vision deficiency. The first five SciencePlots default colours (#0c5da5, #00b945, #ff9500, #ff2c00, #845b97; the cycle continues with the greys #474747 and #9e9e9e) are widely used in published figures. Under simulated protanopia their green and orange are 3.7 CIEDE2000 units apart (4.9 to 5.6 under other common simulation models): too close to tell apart reliably.

The author wanted the [Rang](https://github.com/mohsennasab/Rang) palettes, whose colours are drawn from Persian, Iranian and Persianate art and culture and whose values are released under CC0.

**How separation is measured here:** CIEDE2000 colour difference between every pair of colours, under normal vision and under simulated protanopia, deuteranopia and tritanopia (Machado et al. 2009, severity 1.0, applied to linear sRGB with out-of-gamut values clipped). A palette's score is its closest pair over all four. As house conventions, a score below 8 fails and 10 or more is the target.

## Decision

- **Default categorical palette `vf.qual`:** #333a80, #d96e4c, #598fb6, #603d34, #b0472c, #4a657f, in that order.
  - **Candidate pool.** The six come from the 32 Rang colours (of 93) that meet all of these:
    - at least 3:1 contrast on white;
    - CIELAB lightness between 25 and 70;
    - chroma of at least 15;
    - a shift of at most 3 CIEDE2000 units in an sRGB to FOGRA39 to sRGB round trip (relative colorimetric);
    - at least 12 units from the greys #808080 and #C7C7C7.
  - **Search.** An exhaustive search found a four-colour set whose closest pair is as large as possible (24.9, tied with other sets). The fifth and sixth colours were then added to keep the closest pair as large as possible given the first four.
- **Separation by number of categories.** The first four colours stay at least 24.9 apart under every vision type. With five or six categories the closest pair falls to 13.6 and 12.2: still above the target, but the reds and blues start to look related. From the fifth category on, templates add a marker or line-style difference as well.
- **Greyscale.** `vf.qual` is not separated by lightness: #d96e4c and #598fb6 differ by 1.2 in CIELAB lightness, and #333a80 and #603d34 by 2.1. Figures meant for greyscale printing need markers or line styles from the third category on.
- **Grey has one meaning.** Observed or reference data use #808080, which is at least 16 units from every `vf.qual` colour. The darker grey #474747 is not used with `vf.qual`, because it is only 7.97 from #603d34 under simulated protanopia, below the fail line of 8.
- **`vf.science_safe`:** the SciencePlots colours adjusted for colour vision deficiency: #0c5da5, #33a964, #db7e00, #da2500, #8a678c.
  - **What changes.** The hue order is kept. Blue is unchanged. Orange and red keep their hue angle but are 8 to 10 units darker. Green and purple lose about a third of their chroma and turn about 8 degrees in hue.
  - **Separation.** The closest pair improves from 3.7 to 11.0. Every colour has at least 3:1 contrast on white, with green and orange exactly at 3.0:1.
  - **Greyscale.** The adjustment puts green and orange at the same lightness (L* 61.65 and 61.64) and red and purple within 1 unit (47.3 and 48.3). In greyscale it therefore separates worse than the original (smallest lightness gap 5.5 before, 0.01 after), so greyscale printing needs dashes or markers.
- **Legacy palettes** are available for reproducing figures that are already published; using them raises a warning.
- The Rang values are copied into Visualific unchanged, with credit to Rang and its author.

## Consequences

- Colour separation will be tested when the palettes arrive in v0.1. Each palette must reach the house fail line of 8, and its measured score is also pinned with a margin of about 1 unit, so that a change to the palette or to the simulation code fails a test.
- The separation figures depend on the simulation model and its implementation. The Viénot et al. (1999) model, with the Smith-Pokorny cone fundamentals of the original paper, gives protan and deutan values within about 1 unit of these, and applying the Machado matrices to gamma-encoded instead of linear RGB changes them by up to about 3 units (the SciencePlots green and orange go from 3.7 to 6.9).
- Swatch distances overstate how distinguishable thin lines are (Stone, Szafir and Setlur 2014). The documentation shows palettes as line samples.
- Copying the Rang values adds CC0-1.0 to the package licence: it becomes `MIT AND OFL-1.1 AND CC0-1.0`, with Rang's notice in `LICENSES/`.

## References

- Birch, J. (2012). Worldwide prevalence of red-green color deficiency. *Journal of the Optical Society of America A*, 29(3), 313–320. https://doi.org/10.1364/JOSAA.29.000313
- Machado, G. M., Oliveira, M. M. and Fernandes, L. A. F. (2009). A physiologically-based model for simulation of color vision deficiency. *IEEE Transactions on Visualization and Computer Graphics*, 15(6), 1291–1298. https://doi.org/10.1109/TVCG.2009.113
- Sharma, G., Wu, W. and Dalal, E. N. (2005). The CIEDE2000 color-difference formula: implementation notes, supplementary test data, and mathematical observations. *Color Research & Application*, 30(1), 21–30. https://doi.org/10.1002/col.20070
- Stone, M., Szafir, D. A. and Setlur, V. (2014). An engineering model for color difference as a function of size. *Proceedings of the IS&T Color and Imaging Conference*, 22, 253–258. https://doi.org/10.2352/CIC.2014.22.1.art00045
- Viénot, F., Brettel, H. and Mollon, J. D. (1999). Digital video colourmaps for checking the legibility of displays by dichromats. *Color Research & Application*, 24(4), 243–252. <https://doi.org/10.1002/(SICI)1520-6378(199908)24:4%3C243::AID-COL5%3E3.0.CO;2-3>
