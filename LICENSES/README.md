# Licences

Visualific contains three kinds of material under three licences. The package licence is the SPDX expression `MIT AND OFL-1.1 AND CC0-1.0`.

| Material | Files | Licence |
|---|---|---|
| Visualific's code and documentation | everything else, apart from the licence texts in this folder | MIT, in [`LICENSE`](../LICENSE) |
| Liberation Serif 2.1.5 (Regular, Bold, Italic, Bold Italic), unmodified | `src/visualific/fonts/LiberationSerif-*.ttf` | SIL Open Font License 1.1, in [`OFL-1.1.txt`](OFL-1.1.txt) (also shipped as `src/visualific/fonts/OFL.txt`) |
| Palette names, colour values and orders from Rang 0.3.0 | `src/visualific/palettes/rang.json` | CC0 1.0 Universal, in [`CC0-1.0.txt`](CC0-1.0.txt) |

## Liberation Serif

Liberation Serif is a font by Steve Matteson (Ascender) and Red Hat, with character widths matching Times New Roman. The font files are the official release `liberation-fonts-ttf-2.1.5.tar.gz` from <https://github.com/liberationfonts/liberation-fonts/releases/tag/2.1.5>, copied without change. Their copyright notice is at the top of `OFL-1.1.txt`: digitized data copyright (c) 2010 Google Corporation, with Reserved Font Arimo, Tinos and Cousine; copyright (c) 2012 Red Hat, Inc., with Reserved Font Name Liberation. Visualific uses the font when Times New Roman is not installed, and documents produced with it are not covered by the font licence.

## Rang palette values

The colours behind `vf.qual`, `vf.termeh`, `vf.rostan` and `vf.mina_div` come from [Rang](https://github.com/mohsennasab/Rang), colour palettes drawn from Persian art, by Mohsen Tahmasebi Nasab. Rang dedicates its palette names, colour values, descriptions and orders to the public domain under CC0 1.0. `rang.json` holds the names, colour values and orders of all eleven palettes as they stand at Rang commit `f30cbd7` (version 0.3.0), unchanged. CC0 does not require credit; Visualific gives it anyway. Rang's code (MIT), source photographs and logo are not part of Visualific.
