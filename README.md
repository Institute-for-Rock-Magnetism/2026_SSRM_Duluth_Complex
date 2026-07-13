# 2026 IRM Summer School of Rock Magnetism — Duluth Complex project

Five small groups are each characterizing the rock magnetic properties of a distinct lithologic unit of the Duluth Complex, sampled from drill core D-6A. This page collects what you need to get started: your group, your interval, and the instrument schedule. The core itself, the 1992 drill log, the samples, and the measured data are documented in the pages linked below.

These materials are rendered as a web book at [institute-for-rock-magnetism.github.io/2026_SSRM_Duluth_Complex](https://institute-for-rock-magnetism.github.io/2026_SSRM_Duluth_Complex/), where the stratigraphic column and susceptibility figures are generated from the data files in this repository.

![Stratigraphic column of drill hole D-6A from the Severson (1992) log, with the depths of the May 2026 samples, the Exxon (1979) Cu-Ni-Co assays, and the KT-10 magnetic susceptibility profile measured on the split core. The stratigraphic units labeled down the left side of the column are the intervals assigned to the five groups.](D-6A_log/D_6A_plot_primary.png)

The whole hole at a glance: lithology, the samples taken in May 2026, the historical geochemistry, and the susceptibility profile. The [stratigraphic column notebook](D-6A_log/D_6A_stratigraphic_column.ipynb) builds this figure from the CSV files in the repository and also summarizes susceptibility by facies.

## Groups

| Group | Project | Participants |
|---|---|---|
| 1 | Main Augite Troctolite | Alexis, Gabriel, Gianna, Oscar |
| 2 | Ultramafic (U1 and U3) | Allison, Margaret, Ricardo, Roshini |
| 3 | BAN (Basal Augite Troctolite and Norite) | Ana, Lily, Paige, Taizo |
| 4 | Heterogeneous (basal heterogeneous zone) | Ellen, Nay, Rachel, Yogaraj |
| 5 | Felsic (Giants Range Batholith + granophyre) | Julia, Nicole, Peter, Tolulope |

## Instrument schedule

Each group rotates through the five instrument stations over the week of July 20–24, 2026, so that each group works on every instrument.

| Day | Group 1 | Group 2 | Group 3 | Group 4 | Group 5 |
|---|---|---|---|---|---|
| **Day 1** — Monday, July 20 | Lake Shore VSM | MPMS | RAPID SRM | Kappabridges | QDM |
| **Day 2** — Tuesday, July 21 | MPMS | RAPID SRM | Kappabridges | QDM | Lake Shore VSM |
| **Day 3** — Wednesday, July 22 | RAPID SRM | Kappabridges | QDM | Lake Shore VSM | MPMS |
| **Day 4** — Thursday, July 23 | Kappabridges | QDM | Lake Shore VSM | MPMS | RAPID SRM |
| **Day 5** — Friday, July 24 | QDM | Lake Shore VSM | MPMS | RAPID SRM | Kappabridges |

*For analyses on Monday, July 27 and Tuesday, July 28 we will prioritize what experiments are the highest priority for each group.*

## Project intervals

Depths are depth from collar in feet, and unit boundaries follow the Severson (1992) log as tabulated in [`D_6A_section_primary.csv`](D-6A_log/D_6A_section_primary.csv). Sample counts are the May 2026 samples falling in each unit; the full table is in [`D-6A_samples.csv`](D-6A_sampling/D-6A_samples.csv).

| Group | Unit(s) | Interval (ft) | Samples |
|---|---|---|---|
| 1 — Main Augite Troctolite | MAIN AGT | 124–1297 | 37 |
| 2 — Ultramafic | U1; U3 | 1297–1463; 1817–1872 | 17 |
| 3 — BAN | BAN (u); BAN (l) | 1725–1817; 1872–2050 | 11 |
| 4 — Heterogeneous | BH (u); BH | 1463–1605; 1695–1725 | 12 |
| 5 — Felsic | GRAN, plus granophyre and the oxidized augite troctolite at D6A-420 | 2050–2125, plus xenolith intervals | 6 |

Specimens are being prepared from the May 2026 samples by Marcus Lorenzen; the preparation scheme is described in the [sampling documentation](D-6A_sampling/sampling.md#sample-prep-plans).

Two aspects of the sampling bear on what each group can do. The Ultramafic and Heterogeneous intervals were only partially sampleable — the core survives as quarter core from 1354–1445 ft and 1625–1692 ft, which precluded drilling paleomagnetic cores there. The May 2026 observations also place two contacts differently from the Severson log: the Giants Range Batholith contact at 2030 ft rather than 2038 ft, and the U3–BAN transition at 1872 ft rather than 1900 ft. Both differences matter for how Groups 2, 3, and 5 assign specimens to units, and are recorded in the [May 2026 core notes](D-6A_sampling/sampling.md#additional-notes).

## Research goals

The projects are organized around rock magnetic characterization of the distinct lithologic units intersected by the core, with each group taking on one unit of the layered series. Working through a common suite of experiments on contrasting lithologies — from the main augite troctolite, through the ultramafic and heterogeneous units, to the basal norite and the granitic footwall — allows the magnetic mineralogy, domain state, and remanence-carrying behavior of each unit to be established and then compared across the intrusion.

Characterizing the units in this way is motivated by a set of broader questions that the assembled data can begin to address: how the ratio of remanent to induced magnetization varies between units and what that implies for interpretation of the aeromagnetic field over the Duluth Complex; how serpentinization has modified the magnetic mineralogy of the olivine-rich units; whether remanence is carried by inclusions hosted within silicate phases or by interstitial oxides, and how that partitioning differs between lithologies; what the oxide- and sulfide-rich basal cumulates record; and how laboratory susceptibility on prepared specimens compares with the susceptibility measured downhole on the split core.

The [geologic background](duluth_complex_background.md) page sets out the Midcontinent Rift and Duluth Complex context, including why the ultramafic units and the basal contact are of particular rock magnetic interest.

## The core in brief

D-6A is an exploration hole in the Dunka Pit area of the South Kawishiwi intrusion, part of the ca. 1096 Ma Duluth Complex of northeastern Minnesota. It is a vertical hole with an end-of-hole depth of 2125 ft that penetrates the troctolitic layered series of the intrusion — anorthositic troctolite, augite troctolite, and ultramafic units — and bottoms in the Archean Giants Range Batholith footwall. It was logged by Mark Severson (NRRI) in 1992, and geochemical datasets developed from the core are archived here alongside the log.

The core was examined and sampled at the Minnesota DNR Drill Core Library in Hibbing, Minnesota, from May 26 to 28, 2026, when the KT-10 magnetic susceptibility profile was also measured. Full details of the hole, the core examination, and the sampling are in the [core examination and sampling](D-6A_sampling/sampling.md) page.

## Repository structure

| Path | Contents |
|---|---|
| [duluth_complex_background.md](duluth_complex_background.md) | Geologic background on the Midcontinent Rift, the Duluth Complex, and the South Kawishiwi intrusion |
| [D-6A_log/](D-6A_log/D_6A_stratigraphic_column.ipynb) | Mark Severson's 1992 log and derived products: pystrat-ready stratigraphic section CSVs, a facies style palette, transcribed geochemistry datasets, the plotting script, and a [notebook that renders the stratigraphic column](D-6A_log/D_6A_stratigraphic_column.ipynb). The file schemas and data conventions are set out in the [data dictionary](D-6A_log/data_dictionary.md), and the codes themselves in the [acronym glossary](D-6A_log/D_6A_log_codes.md) |
| [D-6A_sampling/](D-6A_sampling/sampling.md) | The hole itself, the May 2026 core examination and sampling, the sample table, core-box layout and photo conventions, and specimen preparation plans |
| [D-6A_data/](D-6A_data/measured_data.md) | Measured data collected from the core, including the [KT-10 magnetic susceptibility measurements](D-6A_data/measured_data.md) |
