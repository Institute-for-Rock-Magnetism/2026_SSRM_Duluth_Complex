# 2026_SSRM_Duluth_Complex

This repository contains materials associated with the 2026 IRM Summer School of Rock Magnetism project on the Duluth Complex. The work centers on drill core D-6A from the South Kawishiwi intrusion.

## The D-6A drill core

D-6A (DNRNUM 13933) is an Exxon exploration hole in the Dunka Pit area of the South Kawishiwi intrusion (SKI), part of the 1096 Ma Duluth Complex of northeastern Minnesota. The collar is at 47.6989°N, 91.8362°W (St. Louis County, Minnesota; PLSS location 10-60N-12W), with an end-of-hole depth of 2125 ft. These coordinates are from the Minnesota DNR Drill Core Library boring-location dataset (matched on DNRNUM 13933, reprojected from UTM Zone 15N / EPSG:26915 to WGS84). The Severson log lists a collar elevation of 1521 ft; the DNR dataset gives 1517 ft. The same DNR dataset records the hole as vertical (dip −90°, azimuth 360°), drilled by diamond coring for exploration; this is the as-collared orientation rather than a downhole deviation survey. It penetrates the South Kawishiwi Troctolitic Series — a layered sequence of anorthositic troctolite, augite troctolite, and ultramafic units — and bottoms in the Giants Range Granite footwall. The hole was hand-logged by Mark Severson (NRRI) in 1992 as part of a major effort studying the layered series of the Duluth Complex. There are also geochemical datasets developed from the core that are included in this repository.

## Core examination and sampling (May 26–28, 2026)

The core was examined and sampled at the Minnesota DNR Drill Core Library in Hibbing, Minnesota, by Nick Swanson-Hysell, Mary Yao, and Kate Akin from May 26 to 28, 2026. Mark Severson's 1992 hand log was used as a scaffold for sampling and for additional observations recorded against the core. Where our observations of the split core differed from the log — for example in the placement of unit contacts — those differences are noted (see [D-6A_log/D_6A_log_notes.md](D-6A_log/D_6A_log_notes.md)).

The core has been variably depleted by prior sampling. Some intervals survive only as quarter core, which limited or precluded additional sampling; those intervals are flagged in the log notes and the sample table.

## Magnetic susceptibility measurements

Magnetic susceptibility was measured on the core with a handheld KT-10 susceptibility meter set in half-core mode, configured for NQ core with the standard diameter of 47.6 mm (1.875 inches). Measurements and their depths are archived in [D-6A_data/susceptibility_KT10/](D-6A_data/susceptibility_KT10/).

Several aspects of the core geometry bear on interpretation of these data:

- **Split, not cut.** The half core was roughly split rather than sawn. The splitting used a vise-type instrument, which carries some potential for magnetic overprinting of the core surface (potentially important for remanence interpretations).
- **Uneven surface.** Because the core was broken rather than cut, the measured surface was not perfectly flat but was instead variably uneven. We sought out the flattest available surfaces for each measurement, but residual unevenness departs from the flat-surface geometry assumed by the half-core correction.
- **Quarter-core intervals.** Where only quarter core remained rather than half core, we combined quarter core from two adjacent quarter-core pieces to approximate the equivalent of a half core for the measurement.

## Candidate research projects for the IRM Summer School

Candidate small-group rock-magnetic project ideas for the summer school — spanning Koenigsberger ratios for aeromagnetic interpretation, the magnetic signature of serpentinization and its tie to hydrogen generation, silicate-hosted versus interstitial remanence carriers, oxide- and sulfide-rich basal cumulates, and downhole susceptibility ground-truthing — are collected in [research_project_ideas.md](research_project_ideas.md), along with a DOI-verified reference list.

## Repository structure

| Path | Contents |
|---|---|
| [D-6A_log/](D-6A_log/) | Mark Severson's 1992 hand log and derived products: pystrat-ready stratigraphic section CSVs, a facies style palette, transcribed geochemistry datasets, an acronym/unit-code glossary, the plotting script, and a rendered stratigraphic plot |
| [D-6A_sampling/](D-6A_sampling/) | Sample table for the May 2026 sampling, core-box layout and photo conventions, and sampling images |
| [D-6A_data/](D-6A_data/) | Measured data collected from the core, including the KT-10 magnetic susceptibility measurements |