"""Build D-6A_specimens.csv from D-6A_samples.csv using the irm_database_template format."""
import csv
from pathlib import Path

ROOT = Path("/Users/penokean/0000_GitHub/2026_SSRM_Duluth_Complex/D-6A_sampling")
SAMPLES = ROOT / "D-6A_samples.csv"
TEMPLATE = ROOT / "irm_database_template.csv"
OUT = ROOT / "D-6A_specimens.csv"

# IRM template headers
with TEMPLATE.open(encoding="utf-8-sig") as f:
    headers = next(csv.reader(f))

# Locality info from README
LOC_ID = "D6A"
LOC_DESC = (
    "D-6A drill core, Dunka Pit area, South Kawishiwi intrusion, "
    "Duluth Complex; collar 47.6989N, 91.8362W (DNRNUM 13933)"
)
SITE_LAT = "47.6989"
SITE_LON = "-91.8362"
EXP_ID = "SSRM 2026"
EXP_DESC = "2026 IRM Summer School of Rock Magnetism, Duluth Complex project"

# Orientation rules by sample type
def orient(sample_type: str):
    t = sample_type.strip().lower()
    # treat 'fill core core' typo as 'full core core'
    if t in ("full core core", "fill core core", "half core core"):
        return ("0", "0")
    if t == "quarter core":
        return ("0", "-90")
    # core chip: leave blank per user direction
    return ("", "")


rows_out = []
with SAMPLES.open(newline="") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if not row or not row[0].strip():
            continue
        sample = row[0].strip()
        footage = row[1].strip()
        stype = row[2].strip()
        sev_unit = row[3].strip()
        sev_desc = row[4].strip()
        rock_type = row[5].strip()
        sulfide = row[6].strip()
        our_desc = row[7].strip()

        sample_desc = our_desc
        site_desc_parts = [p for p in (
            f"Severson unit {sev_unit}" if sev_unit else "",
            f"Severson description: {sev_desc}" if sev_desc else "",
            f"rock type: {rock_type}" if rock_type else "",
            f"sulfide {sulfide}%" if sulfide else "",
        ) if p]
        site_desc = "; ".join(site_desc_parts)

        az, plg = orient(stype)

        for suffix in ("a", "b"):
            spec_id = f"{sample}{suffix}"
            spec_az = az if suffix == "a" else ""
            spec_plg = plg if suffix == "a" else ""
            spec_desc = (
                "oriented specimen for remanence"
                if suffix == "a"
                else "chip for rock magnetic experiments"
            )
            record = {
                "Specimen_ID": spec_id,
                "Specimen_description": spec_desc,
                "Specimen_azimuth": spec_az,
                "Specimen_plunge": spec_plg,
                "Specimen_mass[g]": "",
                "Specimen_vol[cc]": "",
                "Specimen_coordinate": footage,
                "Uchannel_length[cm]": "",
                "Uchannel_area[cm2]": "",
                "Sample_ID": sample,
                "Sample_description": sample_desc,
                "Site_ID": sample,
                "Site_description": site_desc,
                "Site_lat": SITE_LAT,
                "Site_lon": SITE_LON,
                "Site_coordinate": footage,
                "Site_bedding_dip": "",
                "Site_dip_azimuth": "",
                "Locality_ID": LOC_ID,
                "Locality_description": LOC_DESC,
                "Expedition_ID": EXP_ID,
                "Expedition_description": EXP_DESC,
                "material_ID": "",
                "material_description": "",
                "material_manufacturer": "",
                "material_composition": "",
                "material_mineral_name": "",
                "material_grain_length[um]": "",
                "material_grain_L/W_ratio": "",
                "composition_parameter_X": "",
                "composition_parameter_Y": "",
                "oxidation_parameter_Z": "",
            }
            rows_out.append([record.get(h, "") for h in headers])

with OUT.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows_out)

print(f"Wrote {len(rows_out)} specimen rows ({len(rows_out)//2} samples) to {OUT}")
