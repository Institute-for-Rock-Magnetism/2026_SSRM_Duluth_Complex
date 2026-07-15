"""Build D-6A_specimens.csv and D-6A_ages.csv from D-6A_samples.csv.

D-6A_specimens.csv follows the irm_database_template format. Columns beyond
the IRM template carry fields required by the MagIC database
(sites.geologic_classes, sites.geologic_types, sites.lithologies, sites.age,
samples/sites.method_codes, locations.location_type) with the plan that the
IRM database will add columns for these required outputs.

D-6A_ages.csv is a MagIC-format ages table (one row per age determination)
documenting where the assigned ages come from, so that the age citations
accompany the study without needing citation columns in the magnetics tables.
"""
import csv
from pathlib import Path

ROOT = Path("/Users/penokean/0000_GitHub/2026_SSRM_Duluth_Complex/D-6A_sampling")
SAMPLES = ROOT / "D-6A_samples.csv"
TEMPLATE = ROOT / "irm_database_template.csv"
OUT = ROOT / "D-6A_specimens.csv"
OUT_AGES = ROOT / "D-6A_ages.csv"

# IRM template headers
with TEMPLATE.open(encoding="utf-8-sig") as f:
    headers = next(csv.reader(f))

# Additional columns required for MagIC upload (site level unless noted).
# The Locality_* columns describe the whole core (location level in MagIC).
MAGIC_HEADERS = [
    "Sample_method_codes",      # MagIC samples.method_codes
    "Site_method_codes",        # MagIC sites.method_codes
    "Site_geologic_classes",    # MagIC sites.geologic_classes
    "Site_geologic_types",      # MagIC sites.geologic_types
    "Site_lithologies",         # MagIC sites.lithologies
    "Site_age",                 # MagIC sites.age
    "Site_age_sigma",           # MagIC sites.age_sigma (1 sigma per MagIC convention)
    "Site_age_low",             # MagIC sites.age_low (range from multiple dates)
    "Site_age_high",            # MagIC sites.age_high
    "Site_age_unit",            # MagIC sites.age_unit
    "Locality_type",            # MagIC locations.location_type
    "Locality_geologic_classes",
    "Locality_lithologies",
    "Locality_age",
    "Locality_age_sigma",
    "Locality_age_low",         # used when a locality spans multiple ages
    "Locality_age_high",
    "Locality_age_unit",
]
headers = headers + MAGIC_HEADERS

# Core info from README
CORE_DESC = (
    "D-6A drill core, Dunka Pit area, South Kawishiwi intrusion, "
    "Duluth Complex; collar 47.6989N, 91.8362W (DNRNUM 13933)"
)
SITE_LAT = "47.6989"
SITE_LON = "268.1638"  # 91.8362W in the MagIC 0-360 longitude convention
EXP_ID = "SSRM 2026"
EXP_DESC = "2026 IRM Summer School of Rock Magnetism, Duluth Complex project"

# Localities are lithology groups (the IRM Summer School working groups),
# assigned per sample via the 'group' column so that samples can be
# filtered by group within the IRM database
GROUP_TO_LOCALITY = {
    "AGT": ("D6A-AGT", "Group AGT: Main AGT augite troctolite series"),
    "Ultramafic": ("D6A-ultramafic", "Group Ultramafic: ultramafic units U1-U3"),
    "BAN": ("D6A-BAN", "Group BAN: Basal Augite Troctolite and Norite"),
    "BH": ("D6A-BH", "Group BH: basal heterogeneous unit"),
    "Felsic": ("D6A-felsic",
               "Group Felsic: GRB footwall, granophyre, and oxidized augite troctolite"),
}

LOC_TYPE = "Drill Site"
LOC_CLASSES = "Igneous:Intrusive"

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


# read samples, keyed by stripped header names
samples = []
with SAMPLES.open(newline="") as f:
    reader = csv.reader(f)
    sample_headers = [h.strip() for h in next(reader)]
    for row in reader:
        if not row or not row[0].strip():
            continue
        samples.append({h: v.strip() for h, v in zip(sample_headers, row)})

# per-locality (lithology group) aggregates from the member samples:
# lithologies in down-core order; a single age +/- sigma when the member
# sites share one age, otherwise an age_low/age_high span covering all
# member-site ages and age ranges
loc_info = {}
for rec in samples:
    loc_id, loc_group_desc = GROUP_TO_LOCALITY[rec["group"]]
    info = loc_info.setdefault(loc_id, {"liths": [], "ages": {}})
    for lith in rec["lithologies"].split(":"):
        if lith and lith not in info["liths"]:
            info["liths"].append(lith)
    key = (rec["age"], rec["age sigma"], rec["age low"], rec["age high"])
    info["ages"][key] = None  # ordered unique

for loc_id, info in loc_info.items():
    ages = list(info["ages"])
    if len(ages) == 1:
        info["age"], info["age_sigma"], info["age_low"], info["age_high"] = ages[0]
    else:
        values = [float(v) for age, _, low, high in ages
                  for v in (age, low, high) if v]
        info["age"], info["age_sigma"] = "", ""
        info["age_low"], info["age_high"] = f"{min(values):g}", f"{max(values):g}"

rows_out = []
for rec in samples:
    sample = rec["sample name"]
    footage = rec["footage"]
    stype = rec["sample type"]
    sev_unit = rec["Severson unit"]
    sev_desc = rec["Severson description"]
    rock_type = rec["rock type"]
    sulfide = rec["sulfide (%)"]
    our_desc = rec["our description"]

    loc_id, loc_group_desc = GROUP_TO_LOCALITY[rec["group"]]
    loc = loc_info[loc_id]
    loc_desc = f"{loc_group_desc}; {CORE_DESC}"

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
            "Locality_ID": loc_id,
            "Locality_description": loc_desc,
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
            # MagIC-required additions
            "Sample_method_codes": rec["method codes"],
            "Site_method_codes": rec["method codes"],
            "Site_geologic_classes": rec["geologic classes"],
            "Site_geologic_types": rec["geologic types"],
            "Site_lithologies": rec["lithologies"],
            "Site_age": rec["age"],
            "Site_age_sigma": rec["age sigma"],
            "Site_age_low": rec["age low"],
            "Site_age_high": rec["age high"],
            "Site_age_unit": rec["age unit"],
            "Locality_type": LOC_TYPE,
            "Locality_geologic_classes": LOC_CLASSES,
            "Locality_lithologies": ":".join(loc["liths"]),
            "Locality_age": loc["age"],
            "Locality_age_sigma": loc["age_sigma"],
            "Locality_age_low": loc["age_low"],
            "Locality_age_high": loc["age_high"],
            "Locality_age_unit": rec["age unit"],
        }
        rows_out.append([record.get(h, "") for h in headers])

with OUT.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows_out)

print(f"Wrote {len(rows_out)} specimen rows ({len(rows_out)//2} samples) to {OUT}")

# MagIC ages table: one row per age determination documenting the source of
# each assigned age; citations live here rather than in the magnetics tables.
# The sites the age applies to are listed by name in the description.
AGE_DESC_BY_CITATION = {
    "10.1130/G47873.1": (
        "U-Pb zircon date for the Partridge River intrusion of the Duluth "
        "Complex, assigned to the South Kawishiwi intrusion troctolitic "
        "series sites (uncertainty given at 1 sigma per MagIC convention; "
        "reported as +/-0.19 Ma 2 sigma)"
    ),
    "10.1016/j.precamres.2007.02.019": (
        "Weighted mean U-Pb zircon date for the early stage granophyres of "
        "the Duluth Complex felsic series (Cucumber Lake, Misquah Hills, "
        "Whitefish Lake, and Mt. Weber bodies), assigned to the granophyre "
        "sites interpreted as felsic series xenoliths (uncertainty given at "
        "1 sigma per MagIC convention; reported as 1106.9 +/- 1.8 Ma)"
    ),
    "10.1139/e93-217": (
        "Age range spanning U-Pb zircon dates for phases of the Giants Range "
        "batholith (2674 +/- 5 Ma Shannon Lake granite to 2685 +/- 4 Ma "
        "Britt granodiorite), assigned to the batholith footwall sites; the "
        "phase intersected by D-6A is not directly dated"
    ),
}

AGES_HEADERS = ["location", "age", "age_sigma", "age_low", "age_high",
                "age_unit", "method_codes", "citations", "description"]
age_groups = {}  # one entry per age determination, in down-core order
for rec in samples:
    key = (rec["age"], rec["age sigma"], rec["age low"], rec["age high"],
           rec["age unit"], rec["age citation"])
    grp = age_groups.setdefault(key, {"localities": [], "sites": []})
    loc_id = GROUP_TO_LOCALITY[rec["group"]][0]
    if loc_id not in grp["localities"]:
        grp["localities"].append(loc_id)
    grp["sites"].append(rec["sample name"])

ages_rows = []
for (age, sigma, low, high, unit, citation), grp in sorted(
        age_groups.items(), key=lambda kv: float(kv[0][0] or kv[0][2])):
    desc = AGE_DESC_BY_CITATION[citation]
    desc += f"; applies to sites {', '.join(grp['sites'])}"
    ages_rows.append([
        ":".join(grp["localities"]),
        age, sigma, low, high, unit,
        "GM-UPB",
        citation,
        desc,
    ])

with OUT_AGES.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(AGES_HEADERS)
    writer.writerows(ages_rows)

print(f"Wrote {len(ages_rows)} age rows to {OUT_AGES}")
