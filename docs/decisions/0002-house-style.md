# 0002. House style is defined at the final print size

- Status: accepted. The author chose the typeface and the type scale; the assistant derived the line weights and export rules from the author's published figures and took the widths from the publishers' guides.
- Date: 2026-10-15

## Context

Figure code is often written for a large canvas, and the result is reduced to a journal column afterwards. Reduction makes the printed text and lines much smaller than the values written in the code, and the amount differs between figures. `bbox_inches="tight"`, a common matplotlib setting, also changes the saved width so that it no longer matches the declared size.

## Decision

All sizes are set at the final printed size.

- **Typeface:** Times New Roman, falling back to Liberation Serif (metric-compatible with Times New Roman, under the SIL Open Font License 1.1, bundled), then STIXGeneral. Mathematics uses STIX, so no LaTeX installation is needed.
- **Type scale:** 8 pt for tick labels, legends and annotations; 9 pt for axis labels and panel titles; 10 pt bold for panel letters. A compact preset steps each size down by 1 pt (7, 8 and 9 pt) for dense matrices and maps.
- **Sub- and superscripts** are never below 6 pt, in the compact preset too. Matplotlib's mathtext draws scripts at 70 % of the base size, which gives 5.6 pt on an 8 pt tick label, so `vf.use()` enlarges scripts where needed and `vf.check` measures them.
- **Lines:** axes 0.6 pt, data lines 1.2 pt, reference lines 0.8 pt dashed, patch and bar edges 0.5 pt, nothing thinner than 0.3 pt.
- **Widths:** given in millimetres. The initial presets are Elsevier (90, 140 and 190 mm) and Nature (89 and 183 mm), each with its source page and access date.
- **Layout and export:** constrained layout, no `bbox_inches="tight"`. The saved width must match the declared width within 0.5 mm. The file to submit is a PDF with TrueType (Type 42) fonts; a 600 dpi PNG is written for previews. TIFF is available, with its resolution set by content type (Elsevier asks for 1000 dpi for line art).
- **Legend:** no frame, at most one per figure; direct labels are preferred.

## Consequences

- A figure's code shows the sizes the reader will actually see.
- Times New Roman cannot be redistributed. Linux test runs and Colab use the bundled Liberation Serif, while Windows and macOS runs use Times New Roman. The character widths match, so line breaks and layout match closely, but glyph shapes differ. Image tests therefore run on one pinned Linux job.
- Nature asks for Arial or Helvetica at 5 to 7 pt. A Nature profile must switch the typeface and lower the type scale; the house style stays serif at 8 to 10 pt.
- Bundling Liberation Serif adds the SIL Open Font License to the package licence (`MIT AND OFL-1.1`), and the font ships unmodified.
