# D-6A measured data

Data measured on drill core D-6A at the Minnesota DNR Drill Core Library and at the Institute for Rock Magnetism. Depths are given as depth from collar in feet so that they can be cross-referenced against the [stratigraphic section](../D-6A_log/D_6A_stratigraphic_column.ipynb) and the [sample table](../D-6A_sampling/sampling.md).

## Magnetic susceptibility (`susceptibility_KT10/`)

[`susceptibility_KT10/D-6A_KT10_susceptibility.csv`](susceptibility_KT10/D-6A_KT10_susceptibility.csv) holds the down-core magnetic susceptibility profile measured with a handheld KT-10 susceptibility meter during the May 2026 core examination.

| Column | Description |
|---|---|
| `Depth` | Depth from collar, in feet |
| `Susceptibility (10^-3 SI)` | Volume magnetic susceptibility, in units of 10⁻³ SI, as reported by the instrument |
| `Other notes` | Free-text note recorded at the time of measurement (e.g. lithology observed at the measurement point) |

The meter was set in half-core mode and configured for NQ core with the standard diameter of 47.6 mm (1.875 inches). Three aspects of the core geometry bear on interpretation of these values, and are described in more detail in the [repository overview](../README.md):

- The core was roughly split rather than sawn, so the measured surface departs from the flat-surface geometry assumed by the half-core correction.
- The splitting was done with a hydraulic vise-type instrument, which carries some potential for magnetic overprinting of the core surface.
- Where only quarter core remained, quarter core from two adjacent pieces was combined to approximate a half core for the measurement.

The values are therefore best treated as a relative down-core profile rather than as absolute susceptibilities.

The profile is plotted against the lithologic column, and summarized by facies, in the [stratigraphic column notebook](../D-6A_log/D_6A_stratigraphic_column.ipynb).
