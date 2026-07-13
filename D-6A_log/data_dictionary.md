# Data dictionary

Schemas and conventions for the data files in [`D-6A_log/`](D_6A_stratigraphic_column.ipynb). All of these derive from Mark Severson's 1992 hand-logged drill log for D-6A and the geochemistry datasets bound with it. The [stratigraphic column notebook](D_6A_stratigraphic_column.ipynb) reads these files directly and is the best worked example of using them.

## Conventions that apply throughout

**Depths are in feet from collar.** Top of hole is 0 ft; end of hole is 2125 ft. Rows are ordered **top-down**, so the files read in the same order as the original log.

**Below-detection values are stored as negative numbers**, with magnitude equal to the detection limit. `Au_ppm = -0.02` means "below detection, with a detection limit of 0.02 ppm." This preserves the detection limit rather than discarding it. **Filter to `value > 0` before plotting or computing statistics** — treating these as real concentrations will produce nonsense.

**Facies codes are a logging convention.** They follow the modal classification scheme of Phinney (1972) as used by Severson. Full definitions are in the [acronym glossary](D_6A_log_codes.md), and full rock names are mapped in `D_6A_facies_names.csv`.

## Stratigraphic section

`D_6A_section_primary.csv` (46 rows) and `D_6A_section_detailed.csv` (137 rows) share a schema. The primary file is at the granularity of the leftmost from–to column of the log, matching Severson's intended unit divisions. The detailed file splits at every named lithologic sub-interval, preserving embedded granophyre lenses, hornfels stringers, dunite bands, and the like.

| Column | Description |
|---|---|
| `DEPTH_FROM_FT` | Top of the interval, in feet from collar |
| `DEPTH_TO_FT` | Base of the interval, in feet from collar |
| `THICKNESS` | `DEPTH_TO_FT − DEPTH_FROM_FT`. This is the column [pystrat](https://pystrat.readthedocs.io/) consumes |
| `FACIES` | Rock-type code (e.g. `AT`, `AGT`, `PIC`, `FP`); see `D_6A_facies_names.csv` |
| `FORMATION` | South Kawishiwi intrusion stratigraphic unit (see below) |
| `GROUP` | Top-level container: `OVERBURDEN`, `SKI` (South Kawishiwi intrusion), or `FOOTWALL` |
| `DESCRIPTION` | Severson's annotation for the interval. Commas are replaced with semicolons, inch-marks are spelled out, and arrows are written as `->` |

`FORMATION` values, after Severson (1994), are the units the five summer school group projects are organized around:

| Value | Unit |
|---|---|
| `OVB` | Overburden (Quaternary cover) |
| `MAIN AGT` | Main Augite Troctolite |
| `U1`, `U2`, `U3` | Ultramafic One, Two, and Three |
| `BH (u)`, `BH` | Basal Heterogeneous, upper and lower |
| `BAN (u)`, `BAN (l)` | Basal Augite Troctolite and Norite, upper and lower (split by the U3 ultramafic unit) |
| `GRAN` | Giants Range Batholith granitic footwall |

## Facies palette and names

`D_6A_style.csv` (23 rows) is the plotting palette, one row per facies code.

| Column | Description |
|---|---|
| `facies` | Facies code, matching the `FACIES` column of the section files |
| `R`, `G`, `B` | Colour as 0–255 integers. Divide by 255 for matplotlib |
| `width` | Relative column width in the lithologic log; scales loosely with felsic-ness, so the column carries a visual signal of differentiation |
| `swatch` | Human-readable colour name, for reference only |

`D_6A_facies_names.csv` (23 rows) maps each `facies` code to its full rock `name`. It is the single source of truth for those names, and is read by both the figure legend and the notebook tables.

## Geochemistry

Three geochemistry files share the same depth columns: `SAMPLE`, `DEPTH_FROM_FT`, `DEPTH_TO_FT`, and `DEPTH_MID_FT`. Use `DEPTH_MID_FT` as the depth coordinate when plotting against the section. Concentration units are given by the column suffix: `_pct` is weight percent, `_ppm` is parts per million, `_ppb` is parts per billion. Remember that below-detection values are negative.

| File | Rows | Contents |
|---|---|---|
| [`D_6A_geochem_exxon.csv`](D_6A_geochem_exxon.csv) | 101 | Exxon 1979 assays: Cu, Ni, Co, Ag, Au. The only dataset with full-hole coverage (124–2125 ft, on 10–55 ft intervals). Cu and Ni are given in both `_pct` and `_ppm` form |
| [`D_6A_geochem_dnr_pge.csv`](D_6A_geochem_dnr_pge.csv) | 7 | MN DNR Project 255-1/265/266 PGE package: Pt, Pd, Au, plus S, base metals, and majors. **Partial** — the full D-6A suite is roughly 25 samples |
| [`D_6A_geochem_icpms_xrf.csv`](D_6A_geochem_icpms_xrf.csv) | 9 | Follow-up ICP-MS and XRF data on thin-section samples: PGEs, trace metals, and majors. **Partial** |

The two partial datasets carry a `LITH_DESC` column with the sampled lithology as described in the source report.

Two cautions on the geochemistry. The DNR and ICP-MS/XRF tables are transcribed from scanned 1990s assay reports and should be checked against the originals before values are cited. More importantly, many of the DNR samples were collected **across contacts between divergent rock types** (M. Severson, pers. comm., 2026), so a whole-rock value may average two lithologies. Cross-check each sample's `DEPTH_FROM_FT`–`DEPTH_TO_FT` against the section file before treating a concentration as representative of a single facies.

## Related files

The sample table is documented in [core examination and sampling](../D-6A_sampling/sampling.md), and the KT-10 magnetic susceptibility profile in [measured data](../D-6A_data/measured_data.md). The scanned log itself is [`D_6A.pdf`](D_6A.pdf), and Severson's Plate III, which is the canonical legend for the unit and rock-type codes, is [`PLATE3_hung_strat_Dunka_Pit.pdf`](PLATE3_hung_strat_Dunka_Pit.pdf).
