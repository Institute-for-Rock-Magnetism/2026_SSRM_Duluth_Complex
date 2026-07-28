#!/usr/bin/env python
"""Add mass and volume normalization to converted RAPID SRM MagIC tables.

The ``cit`` conversion writes only the raw magnetic moment (``magn_moment``,
Am^2) into the measurements table, and — because the RAPID ``.sam`` orientation
field carries the specimen *mass* (grams) that was entered as the instrument
``Vol`` — it mislabels that mass as ``volume`` in the specimens table. The raw
moment itself is correct (the instrument divides the moment by that value and
``cit`` multiplies it back; see the group notes), but no honest normalization
metadata survives.

This module repairs and extends the converted tables so the three MagIC data
model representations of intensity are all present:

    magn_moment  (Am^2)     raw moment                       -- already written
    magn_mass    (Am^2/kg)  moment / specimen weight         -- added here
    magn_volume  (A/m)      moment / specimen volume         -- added here

It does two things to a converted site folder:

1. Specimens table: set ``weight`` (kg) from the measured specimen mass and
   ``volume`` (m^3) from a nominal core volume, overwriting the mass-as-volume
   value cit left behind.
2. Measurements table: divide ``magn_moment`` by the per-specimen weight and
   volume from the specimens table to populate ``magn_mass`` and ``magn_volume``.

Masses come from ``D-6A_specimens.csv`` (``Specimen_mass[g]``). The volume is a
nominal 11 cc standard paleomagnetic core; some D-6A specimens were cut from the
drill core in non-standard geometries, so this is an approximation to revisit
once individual volumes are recorded in ``Specimen_vol[cc]``.
"""

from pathlib import Path
import csv

from pmagpy import pmag

# 11 cc is the standard paleomagnetic core volume. Some D-6A specimens are
# non-standard (odd geometries cut from the drill core); 11 cc is a nominal
# placeholder applied to every specimen until per-specimen volumes are measured.
NOMINAL_VOLUME_CC = 11.0

# Repo layout: this module lives in D-6A_data/RAPID_SRM/CIT_format/.
_MODULE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _MODULE_DIR.parents[2]
SPECIMENS_CSV = (_REPO_ROOT / "D-6A_sampling" / "IRM_database_prep"
                 / "D-6A_specimens.csv")


def load_masses(specimens_csv=SPECIMENS_CSV):
    """Read specimen masses (grams) from the IRM specimens CSV.

    Args:
        specimens_csv (Path): Path to ``D-6A_specimens.csv``.

    Returns:
        dict: ``Specimen_ID`` -> mass in grams (float), for rows with a
        non-blank ``Specimen_mass[g]``.
    """
    masses = {}
    with open(specimens_csv, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            value = row.get("Specimen_mass[g]", "").strip()
            if value:
                masses[row["Specimen_ID"]] = float(value)
    return masses


def add_normalizations(magic_dir, masses, volume_cc=NOMINAL_VOLUME_CC):
    """Populate specimen weight/volume and measurement mass/volume normalizations.

    Args:
        magic_dir (str or Path): A converted site folder holding ``specimens.txt``
            and ``measurements.txt``.
        masses (dict): ``specimen`` -> mass in grams (from :func:`load_masses`).
        volume_cc (float): Nominal specimen volume in cubic centimeters applied
            to every specimen.

    Returns:
        dict: Counts of records updated, keyed ``specimens``, ``magn_mass``,
        ``magn_volume``.
    """
    magic_dir = Path(magic_dir)
    volume_m3 = volume_cc * 1e-6  # cc -> m^3

    # --- specimens: real weight (kg) and nominal volume (m^3) ---
    specs, _ = pmag.magic_read(str(magic_dir / "specimens.txt"))
    spec_norm = {}  # specimen -> (weight_kg_str, volume_m3_str) for measurement use
    n_weight = 0
    for rec in specs:
        rec["volume"] = "%.3e" % volume_m3
        mass_g = masses.get(rec["specimen"])
        if mass_g is not None:
            rec["weight"] = "%.3e" % (mass_g * 1e-3)  # g -> kg
            n_weight += 1
        else:
            rec["weight"] = ""
        spec_norm[rec["specimen"]] = (rec["weight"], rec["volume"])
    pmag.magic_write(str(magic_dir / "specimens.txt"), specs, "specimens")

    # --- measurements: magn_mass (Am^2/kg) and magn_volume (A/m) ---
    meas, _ = pmag.magic_read(str(magic_dir / "measurements.txt"))
    n_mass = n_vol = 0
    for rec in meas:
        moment = rec.get("magn_moment", "").strip()
        weight, volume = spec_norm.get(rec["specimen"], ("", ""))
        if moment and volume:
            rec["magn_volume"] = "%.3e" % (float(moment) / float(volume))
            n_vol += 1
        if moment and weight:
            rec["magn_mass"] = "%.3e" % (float(moment) / float(weight))
            n_mass += 1
    pmag.magic_write(str(magic_dir / "measurements.txt"), meas, "measurements")

    return {"specimens": n_weight, "magn_mass": n_mass, "magn_volume": n_vol}


def main():
    """Apply normalizations to every converted site under ``MagIC_format``."""
    magic_root = _MODULE_DIR.parent / "MagIC_format"
    masses = load_masses()
    for site_dir in sorted(p for p in magic_root.iterdir() if p.is_dir()):
        if not (site_dir / "specimens.txt").exists():
            continue
        counts = add_normalizations(site_dir, masses)
        print(f"{site_dir.name}: weight set for {counts['specimens']} specimens; "
              f"magn_mass {counts['magn_mass']}, magn_volume {counts['magn_volume']} "
              f"measurements")


if __name__ == "__main__":
    main()
