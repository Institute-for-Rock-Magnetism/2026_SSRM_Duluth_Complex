# D-6A pystrat input files

Stratigraphic and geochemical data for drill hole D-6A (Dunka Pit area, South Kawishiwi intrusion, Duluth Complex), formatted for plotting with [pystrat](https://pystrat.readthedocs.io/).

Source: M. Severson 1992 hand-logged drill log [`D_6A.pdf`](../../D_6A.pdf) plus three nested geochemistry datasets bound with the log (Exxon 1979 assays, MN DNR Project 255-1/265/266 PGE package, follow-up ICP-MS / XRF thin-section data). Acronym definitions and stratigraphic-unit codes resolved in [`../D_6A_log_codes.md`](../D_6A_log_codes.md).

EOH = 2125 ft. Granitic footwall (Giants Range Granite, locally Qtz Monzonite) starts ~2050 ft.

## Files

| File | Rows | Purpose |
|---|---|---|
| `D_6A_section_primary.csv` | 42 | Lithologic section at the primary-interval granularity (leftmost from-to column of the log; matches Severson's intended unit granularity) |
| `D_6A_section_detailed.csv` | 137 | Lithologic section split at every named lithologic sub-interval (preserves embedded granophyre lenses, hornfels stringers, dunite bands, etc.) |
| `D_6A_style.csv` | 23 | Facies palette: `facies, R, G, B, width` rows for every unique facies in either section file |
| `D_6A_geochem_exxon.csv` | 101 | Exxon 1979 Cu/Ni/Co/Ag/Au assays — full depth coverage 124–2125 ft on 10–55 ft intervals |
| `D_6A_geochem_dnr_pge.csv` | 7 | MN DNR Project 255-1/265/266 (Dahlberg, Peterson, and Frey, 1988–89) PGE / Bondar-Clegg package. **PARTIAL** — captures the D-6A rows transcribed from the bound back-pages; the full Project 255-1 D-6A suite has ~25 samples. Download the DNR GIS raw-data zip for the complete table: https://files.dnr.state.mn.us/lands_minerals/mpes_projects/mpes255_1_265_266.zip |
| `D_6A_geochem_icpms_xrf.csv` | 9 | Follow-up ICP-MS / XRF thin-section data on D-6A samples (PGEs + trace metals + majors). **PARTIAL** — transcribed from the multi-page hand-annotated back-pages tables; values flagged as best-effort reads from a scanned 1990s assay report |

## Section file schema

```
DEPTH_FROM_FT, DEPTH_TO_FT, THICKNESS, FACIES, FORMATION, GROUP, DESCRIPTION
```

- `DEPTH_FROM_FT`, `DEPTH_TO_FT` — depth-from-collar in feet, matching the leftmost columns of the original log. Top of hole = 0, EOH = 2125. Rows are ordered **top-down**, so you can read the CSV directly against the log.
- `THICKNESS` = `DEPTH_TO_FT − DEPTH_FROM_FT`. This is the column pystrat actually consumes.
- `FACIES` — short rock-type code (e.g. `AT`, `AGT`, `PIC`, `FP`). All codes mapped in `D_6A_style.csv`. See [`../D_6A_log_codes.md`](../D_6A_log_codes.md) for full definitions.
- `FORMATION` — formal South Kawishiwi Troctolitic Series (SKTS) stratigraphic unit per Severson (1994, NRRI TR-1993-34): `MAIN_AGT`, `ULTRA_1`, `BOTTOM_HET`, `ULTRA_2`, `LOW_AGT`, `ULTRA_3`, `BAN` (Basal Augite-troctolite + Norite), plus `GRAN` (Giants Range Granite footwall) and `OVERBURDEN`.
- `GROUP` — top-level container: `OVERBURDEN`, `SKI` (South Kawishiwi intrusion), or `FOOTWALL`.
- `DESCRIPTION` — Severson's annotation (commas replaced with semicolons; inch-marks spelled out; arrows written as `->`).

## Style file schema

```
facies, R, G, B, width, swatch
```

Palette designed so related facies have related colors:
- **Anorthositic-troctolitic** family (AT, AAT, AT_T, T): light teal → green gradient as plagioclase decreases and olivine increases
- **Augite-troctolitic / gabbroic** family (AGT_OG, AGT, GA, MELAGAB): olive-green darkening with increasing cpx
- **Ultramafic** family (PIC, FP, PER, DUN): increasingly dark green (DUN nearly black) as plag drops below 20%
- **Olivine-rich troctolite** (ORT, T_ORT): muted dark green between T and PIC, reflecting the 40–50% olivine mode (sits between troctolite and picrite in the ultramafic transition)
- **Felsic intrusives** (PEG, GRANO, QMONZ, GA_A): pink/salmon family
- **Metamorphic/xenolith** (HNFL, HBLD): dark gray-green
- **Overburden / heterogeneous mixed** (OVB, HET): tan / neutral gray

Column widths scale loosely with felsic-ness (ultramafics narrower, felsics wider) so the column carries a visual signal of differentiation.

## Geochem file schemas

All geochem files use `DEPTH_FROM_FT`, `DEPTH_TO_FT`, `DEPTH_MID_FT` to identify the sample interval. `DEPTH_MID_FT` is the natural x-coordinate for `plot_data_attribute`.

Conventions:
- Concentrations are stored as numbers in the units indicated by the column suffix (`_pct` = wt%, `_ppm` = parts per million, `_ppb` = parts per billion).
- **Below-detection-limit (BDL) values are stored as negative numbers** with magnitude equal to the detection limit. Example: `Au_ppm = -0.02` means "<0.02 ppm Au". This preserves the detection-limit information; filter `value > 0` for clean plotting.

## Plotting in pystrat

The section CSVs are ordered top-down (depth 0 → EOH). pystrat treats the first row as the **base** of the section and stacks upward, so to display in core coordinates (depth-down on the y-axis) you can either:

**Option A — invert the y-axis after plotting (recommended; keeps depth values as y-tick labels):**

```python
import pandas as pd
import matplotlib.pyplot as plt
import pystrat

section_df = pd.read_csv('D_6A_section_primary.csv')
style_df   = pd.read_csv('D_6A_style.csv')

# Reverse so deepest row is first (pystrat stacks upward from base)
section_df = section_df.iloc[::-1].reset_index(drop=True)

section = pystrat.Section(
    section_df['THICKNESS'],
    section_df['FACIES'],
    units=section_df[['GROUP', 'FORMATION']].values
)
style = pystrat.Style(
    style_df['facies'],
    style_df[['R', 'G', 'B']].values / 255,
    style_df['width']
)

fig, ax = plt.subplots(1, 1, figsize=(3, 12))
section.plot(style, ax=ax, label_units=True, unit_label_wid_tot=0.4)
# Re-label y-ticks to depth (EOH − pystrat height)
EOH = 2125
ticks = ax.get_yticks()
ax.set_yticklabels([f'{EOH - t:.0f}' for t in ticks])
ax.set_ylabel('Depth (ft)')
ax.invert_yaxis()  # depth increasing downward
```

**Option B — keep top-down ordering and invert post-plot:**

```python
section_df = pd.read_csv('D_6A_section_primary.csv')  # don't reverse
section = pystrat.Section(...)
section.plot(style, ax=ax, label_units=True)
ax.invert_yaxis()  # so y-axis runs depth_from_collar 0 → 2125
```

## Plotting geochem alongside the section

```python
exxon = pd.read_csv('D_6A_geochem_exxon.csv')

fig, axes = plt.subplots(1, 4, figsize=(10, 12), sharey=True)
section.plot(style, ax=axes[0], label_units=True)

# Use DEPTH_MID_FT as height; pystrat heights run 0 at base of section
axes[1].plot(exxon['Cu_pct'], EOH - exxon['DEPTH_MID_FT'])
axes[1].set_xlabel('Cu (wt%)')
axes[1].set_xscale('log')

axes[2].plot(exxon['Ni_ppm'], EOH - exxon['DEPTH_MID_FT'])
axes[2].set_xlabel('Ni (ppm)')

# PGE — log scale, only plot above detection
pge = pd.read_csv('D_6A_geochem_dnr_pge.csv')
detected = pge[pge['Pt_ppb'] > 0]
axes[3].plot(detected['Pt_ppb'], EOH - detected['DEPTH_MID_FT'], 'o')
axes[3].set_xlabel('Pt (ppb)')

for ax in axes:
    ax.invert_yaxis()
```

## Notes on transcription confidence

- **Section CSVs (`primary` / `detailed`)**: lithology codes, depths, and stratigraphic-unit labels transcribed from the legible hand-written 1992 log. Mineral mode percentages and sub-interval depths within DESCRIPTION should be verified against the PDF for any depth where you'll cite numbers.
- **Exxon 1979 assays**: 101 samples, full hole coverage. Numbers read from a typed table with reasonable legibility; minor cells (Au, Ag) may have OCR/read ambiguities. The dataset stores both `_pct` and `_ppm` forms of Cu and Ni, with `_ppm = _pct × 10000` consistency verified.
- **DNR 255-1 PGE table**: 7 D-6A rows are partial — full D-6A suite is ~25 samples. The bound back-pages also include the Table III chemistry (CSL 16683–17159 series, depths ~1927–1989 ft in the BAN unit) which is **not yet extracted** here; pull from the DNR GIS package above if those depths are critical.
  - **Sampling caveat (M. Severson, pers. comm.)**: *"Note that many of the Dahlberg geochemistry samples were collected across contacts (often very divergent rock types) so beware of whole rock values."* Cross-check each sample's `DEPTH_FROM_FT`–`DEPTH_TO_FT` against the section file before interpreting whole-rock concentrations as representative of a single facies.
- **ICP-MS / XRF thin-section data**: 9 D-6A rows, mostly transcribed from hand-annotated multi-page sheets where the column headers and sample labels are written in pencil. Values flagged as best-effort reads. Cross-check against the original report before scientific use.

## Acronym key (FACIES values)

| FACIES | Meaning |
|---|---|
| OVB | Overburden / glacial cover |
| AT | Anorthositic troctolite (75/80–95% plag) |
| AAT | Augite-bearing anorthositic troctolite |
| AGT | Augite troctolite |
| AGT_OG | Augite troctolite to olivine gabbro transition |
| T | Troctolite |
| T_ORT | Troctolite to olivine-rich troctolite (transitional, 30–40% olivine) |
| T_NOR | Troctolite to norite |
| AT_T | Anorthositic troctolite to troctolite (transitional) |
| PIC | Picrite (= melatroctolite per Miller et al. 2002) |
| FP | Feldspathic peridotite (10–30% plag) |
| PER | Peridotite (<10% plag) |
| DUN | Dunite |
| ORT | Olivine-rich troctolite (40–50% olivine) |
| GA | Gabbroic anorthosite |
| MELAGAB | Melagabbro (30–50/55% plag) |
| GA_A | Altered gabbroic anorthosite (saussuritized / uralitized) |
| PEG | Pegmatite / pegmatoidal |
| GRANO | Granophyre |
| QMONZ | Quartz monzonite (Giants Range footwall) |
| HNFL | Hornfels (basaltic / cordierite-bearing) |
| HBLD | Hornblendite (oxide-ultramafic intrusion OUI lens) |
| HET | Heterogeneous mixture (e.g. alternating AT+ultramafics; lithology too mixed to assign a single code) |

| FORMATION | Meaning (SKTS unit per Severson 1994 TR-1993-34) |
|---|---|
| OVERBURDEN | Quaternary cover |
| MAIN_AGT | Main Augite Troctolite zone |
| ULTRA_1 | Ultramafic unit 1 |
| BOTTOM_HET | Basal Heterogeneous zone (mix of AT + ultramafics + hornfels) |
| ULTRA_2 | Ultramafic unit 2 |
| LOW_AGT | Lower Augite Troctolite zone |
| ULTRA_3 | Ultramafic unit 3 (peridotite/dunite-dominant) |
| BAN | Basal Augite-troctolite + Norite unit |
| GRAN | Giants Range Granite footwall |
