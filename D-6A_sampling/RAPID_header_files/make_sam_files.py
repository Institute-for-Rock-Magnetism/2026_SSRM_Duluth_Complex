#!/usr/bin/env python
"""Create RAPID (CIT-format) .sam header files for the D-6A a-series specimens.

Reads ../IRM_database_prep/D-6A_specimens.csv, selects the a-series specimens
("oriented specimen for remanence"), and writes one folder per group
(Locality_ID) containing the group's .sam header file and one extensionless
sample file per specimen. File formats follow the output of mk_sam_file.py
(https://github.com/Swanson-Hysell-Group/SAM_Header) so that the files can be
used directly by the IRM RAPID system and the CIT/paleomag conventions.

These specimens are from unoriented drill core, so the core plate strike is
unconstrained and set to 0. The core plate dip follows from the specimen
plunge convention used in the specimens table:
    Specimen_plunge =   0  (specimen axis horizontal) -> core plate dip = 90
    Specimen_plunge = -90  (specimen axis pointing down) -> core plate dip = 0

SYNTAX
    python make_sam_files.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent                # D-6A_sampling/RAPID_header_files
SPECIMENS_CSV = HERE.parent / "IRM_database_prep" / "D-6A_specimens.csv"

SITE_ID = "D6A-"                    # locality prefix; specimen files are SITE_ID + sample
COMMENT = "unoriented drill core"   # written to line 1 of each sample file
LOCAL_DEC = 0.0                     # no declination correction for unoriented core
CORE_STRIKE = 0.0                   # core plate strike unconstrained; set to 0
BEDDING_STRIKE = 90.0               # mk_sam_file.py defaults -> no tilt correction
BEDDING_DIP = 0.0

# Specimen_plunge -> CIT core plate dip
PLUNGE_TO_CORE_DIP = {0.0: 90.0, -90.0: 0.0}


def fw(value, width):
    """Format a value right-justified to a fixed width with a leading space.

    Args:
        value: Numeric value or preformatted string to write.
        width: Field width in characters (excluding the leading space).

    Returns:
        str: ' ' + value right-justified in the given width.
    """
    text = str(value)
    assert len(text) <= width, f"'{text}' exceeds field width {width}"
    return " " + text.rjust(width)


def main():
    with SPECIMENS_CSV.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # a-series specimens grouped by Locality_ID, preserving CSV (depth) order
    groups = {}
    skipped = []
    for row in rows:
        if row["Specimen_description"].strip() != "oriented specimen for remanence":
            continue
        if row["Specimen_plunge"].strip() == "":
            skipped.append(row["Specimen_ID"])
            continue
        groups.setdefault(row["Locality_ID"], []).append(row)

    for group, specimens in groups.items():
        group_dir = HERE / group
        group_dir.mkdir(exist_ok=True)

        site_lat = float(specimens[0]["Site_lat"])
        site_lon = float(specimens[0]["Site_lon"])

        # .sam header: site name, then lat / lon (0-360) / declination,
        # then one line per sample file
        sam = group + "\r\n"
        sam += " {:.1f} {:05.1f}   {:.1f}\r\n".format(
            round(site_lat, 1), round(site_lon, 1) % 360, LOCAL_DEC)
        for spec in specimens:
            sam += spec["Specimen_ID"] + "\r\n"
        sam_path = group_dir / (group + ".sam")
        with sam_path.open("w", newline="") as f:
            f.write(sam)
        print(f"Writing file - {sam_path}")

        # one extensionless sample file per specimen
        for spec in specimens:
            specimen_id = spec["Specimen_ID"]
            assert specimen_id.startswith(SITE_ID), specimen_id
            sample = specimen_id[len(SITE_ID):]

            plunge = float(spec["Specimen_plunge"])
            core_dip = PLUNGE_TO_CORE_DIP[plunge]

            if spec["Specimen_mass[g]"].strip() == "":
                mass = 1.0
                print(f"no mass found for {specimen_id}, setting to default = 1.0 g")
            else:
                mass = round(float(spec["Specimen_mass[g]"]), 1)

            # strat level: core depth in feet (Specimen_coordinate)
            strat = "{:g}".format(round(float(spec["Specimen_coordinate"]), 1))

            lines = SITE_ID + " " + sample + " " + COMMENT + "\r\n"
            lines += fw(strat, 6)
            lines += fw(CORE_STRIKE, 5)
            lines += fw(core_dip, 5)
            lines += fw(BEDDING_STRIKE, 5)
            lines += fw(BEDDING_DIP, 5)
            lines += fw(mass, 5)
            lines += "\r\n"
            with (group_dir / specimen_id).open("w", newline="") as f:
                f.write(lines)

        # .inp file for later pmagpy CIT import
        inp = "CIT\n"
        inp += ("sam_path\tfield_magic_codes\tlocation\tnaming_convention\t"
                "num_terminal_char\tdont_average_replicate_measurements\t"
                "peak_AF\ttime_stamp\n")
        inp += f"./{group}.sam\tSO-V\t{group}\t2\t1\tTrue\tNone\t0.0\n"
        (group_dir / (group + ".inp")).write_text(inp)

        print(f"{group}: {len(specimens)} specimens")

    if skipped:
        print(f"\nSkipped (no Specimen_plunge in CSV): {', '.join(skipped)}")


if __name__ == "__main__":
    main()
