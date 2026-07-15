"""Build an interactive folium map of drill hole D-6A centered on the bedrock geology.

Drill hole D-6A (DNRNUM 13933), Dunka Pit area, South Kawishiwi intrusion,
Duluth Complex, St. Louis County, Minnesota.

The map is focused on geologic map polygons fetched from the Macrostrat API
(https://macrostrat.org, CC-BY 4.0), which carry the Minnesota Geological
Survey state map unit assignments. Polygons are fetched for the four counties
that cover the Duluth Complex -- Carlton, St. Louis, Lake, and Cook -- using
US Census Bureau cartographic county boundaries to restrict the sampling.
Units are colored by their assignment to named intrusive suites and
supracrustal sequences (Duluth Complex series, Animikie Group, Archean
basement, etc.), following the same classification approach as the 2026
Structure and Tectonics Forum field guide maps. Each polygon is clickable for
unit details, and the geology layer sits over a muted base map so the
polygons read clearly.

Collar coordinates are from the Minnesota DNR Drill Core Library
boring-location dataset (matched on DNRNUM 13933, reprojected from
UTM Zone 15N / EPSG:26915 to WGS84). See the repository root README for
provenance.

Usage:
    python make_location_map.py                  # writes D-6A_location_map.html
    python make_location_map.py --output map.html

The first run queries Macrostrat and caches the polygons to
macrostrat_polygons_D6A.json; later runs use the cache.
"""

import argparse
import json
import math
from pathlib import Path
from urllib.request import urlopen

import folium
import shapefile
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import unary_union
from shapely.prepared import prep

from fetch_macrostrat import fetch_macrostrat_polygons

# D-6A collar, WGS84 (from the DNR boring-location dataset; see module docstring).
D6A_LAT = 47.698863
D6A_LON = -91.836157
D6A_INFO = {
    "name": "D-6A",
    "dnrnum": 13933,
    "eoh_ft": 2125,
    "elev_ft_log": 1521,    # Severson 1992 log
    "elev_ft_dnr": 1517,    # DNR dataset
    "orientation": "vertical (dip -90 deg, azimuth 360 deg)",
    "area": "Dunka Pit, South Kawishiwi intrusion, Duluth Complex",
    "county": "St. Louis County, Minnesota",
}

# ── Geology fetch area ─────────────────────────────────────────────────
# The four counties that cover the Duluth Complex. Restricting the sampling to
# the county outlines (rather than their bounding box) matters: the box would
# spend thousands of queries probing Lake Superior and Ontario, which the
# medium-scale map does not cover. 'large' scale has no Macrostrat coverage
# here; 'medium' carries the Minnesota state map units.
# County outlines are the US Census Bureau 1:500k cartographic boundaries
# (2010 vintage), served as GeoJSON keyed by FIPS code from the plotly
# datasets repository.
COUNTY_FIPS = {
    "27017": "Carlton",
    "27031": "Cook",
    "27075": "Lake",
    "27137": "St. Louis",
}
COUNTIES_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)
HERE = Path(__file__).resolve().parent
COUNTIES_PATH = HERE / "duluth_complex_counties.json"
CACHE_PATH = HERE / "macrostrat_polygons_duluth_counties.json"

# Buffer, in degrees, applied to the county union before sampling, so that
# units straddling the county lines and the Lake Superior shore are captured.
REGION_BUFFER = 0.03

# ── Lake Superior shoreline ────────────────────────────────────────────
# The state bedrock map extends beneath Lake Superior, which reads confusingly
# on an interactive map, so the geology is clipped to the shoreline. This
# shapefile (copied from the 2026 Tectonics Forum field guide GIS data)
# resolves the shore much better than Natural Earth's 10 m coastline, which
# puts headland localities such as Palisade Head ~2 km offshore. Projected in
# NAD83 / UTM zone 15N; converted to lon/lat on load.
LAKE_SHP = HERE / "gis" / "lake_superior_basin.shp"


def _utm15n_to_lonlat(easting, northing):
    """Convert NAD83 / UTM zone 15N coordinates to lon/lat.

    Done with the closed-form Snyder series rather than pyproj because the
    PROJ database in this environment cannot resolve EPSG codes. Accurate to
    well under a meter, and NAD83 is coincident with WGS84 at map scale.

    Args:
        easting: UTM easting in metres.
        northing: UTM northing in metres.

    Returns:
        Tuple of (longitude, latitude) in decimal degrees.
    """
    a = 6378137.0
    f = 1 / 298.257222101  # GRS 1980 ellipsoid (NAD83)
    k0 = 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    x = easting - 500000.0
    mu = (northing / k0) / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (mu
            + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
            + (151 * e1**3 / 96) * math.sin(6 * mu)
            + (1097 * e1**4 / 512) * math.sin(8 * mu))
    c1 = ep2 * math.cos(phi1) ** 2
    t1 = math.tan(phi1) ** 2
    n1 = a / math.sqrt(1 - e2 * math.sin(phi1) ** 2)
    r1 = a * (1 - e2) / (1 - e2 * math.sin(phi1) ** 2) ** 1.5
    d = x / (n1 * k0)
    lat = phi1 - (n1 * math.tan(phi1) / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    lon = (d
           - (1 + 2 * t1 + c1) * d**3 / 6
           + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
           ) / math.cos(phi1)
    return math.degrees(lon) + (15 * 6 - 183), math.degrees(lat)


def load_lake():
    """Load the Lake Superior shoreline polygon in lon/lat.

    The outline is simplified to the same tolerance as the geology polygons,
    so the clipped shoreline matches display resolution and the clipping
    stays fast.

    Returns:
        A shapely geometry of the lake, or None if the shapefile is missing.
    """
    if not LAKE_SHP.exists():
        print(f"  WARNING: {LAKE_SHP.name} not found; geology will not be "
              "clipped to the shoreline")
        return None
    reader = shapefile.Reader(str(LAKE_SHP))
    polys = []
    for shp_rec in reader.shapes():
        pts = shp_rec.points
        if not pts:
            continue
        bounds = list(shp_rec.parts) + [len(pts)]
        rings = [pts[bounds[i]:bounds[i + 1]] for i in range(len(bounds) - 1)]
        rings = [[_utm15n_to_lonlat(x, y) for x, y in ring] for ring in rings]
        rings = [r for r in rings if len(r) >= 4]
        if not rings:
            continue
        poly = Polygon(rings[0], rings[1:]) if len(rings) > 1 else Polygon(rings[0])
        polys.append(poly.buffer(0))
    lake = unary_union(polys)
    return lake.simplify(SIMPLIFY_TOL, preserve_topology=True)


def load_county_region():
    """Load the sampling region: the union of the four Duluth Complex counties.

    The county outlines are downloaded once from the US Census cartographic
    boundary GeoJSON and cached to duluth_complex_counties.json so the map can
    be rebuilt offline.

    Returns:
        A shapely geometry (lon/lat) of the buffered four-county union.
    """
    if COUNTIES_PATH.exists():
        with open(COUNTIES_PATH) as fh:
            counties = json.load(fh)
    else:
        print("Downloading county boundaries (US Census via plotly datasets)...")
        data = json.loads(urlopen(COUNTIES_URL, timeout=60).read())
        counties = [f for f in data["features"] if f["id"] in COUNTY_FIPS]
        found = {f["id"] for f in counties}
        missing = set(COUNTY_FIPS) - found
        if missing:
            raise RuntimeError(f"county FIPS not found in boundary file: {missing}")
        with open(COUNTIES_PATH, "w") as fh:
            json.dump(counties, fh)
        print(f"  cached {len(counties)} county outlines to {COUNTIES_PATH.name}")
    union = unary_union([shape(f["geometry"]) for f in counties])
    return union.buffer(REGION_BUFFER)

# ── Unit groups ────────────────────────────────────────────────────────
# Map units are grouped by their assignment on the source geologic map (carried
# in the Macrostrat ``comments``/``strat_name`` fields), not by lithology, so
# that the Duluth Complex series stay separated from other rift intrusions and
# from basement. Colors follow the 2026 Tectonics Forum field guide maps:
# rift units saturated, pre-rift units desaturated greys.
UNIT_GROUPS = {
    "phanerozoic": ("#efe9c8", "Phanerozoic cover"),
    "kwsed":       ("#dbb96b", "Keweenawan sedimentary rocks"),
    "nsvg":        ("#4e8f43", "North Shore Volcanic Group and related volcanic "
                    "rocks (incl. hornfels at the Duluth Complex roof)"),
    "bbc":         ("#8a5fa8", "Beaver Bay Complex"),
    "dc_felsic":   ("#d98aa0", "Duluth Complex, felsic series"),
    "dc_layered":  ("#2f5f92", "Duluth Complex, layered series"),
    "dc_anorth":   ("#8ba6d6", "Duluth Complex, anorthositic series"),
    "mcr_intr":    ("#4f9a94", "Other Midcontinent Rift intrusions"),
    "animikie":    ("#83806a", "Animikie Group"),
    "paleoprot":   ("#c2bcac", "Other Paleoproterozoic rocks"),
    "archean":     ("#a89f94", "Archean, Superior Province"),
}
CLR_DEFAULT = "#d0ccc0"

# Keweenawan sedimentary and volcanic units keyed on substrings of strat_name
# or name. These must be checked BEFORE the comment rules: their comments
# carry the blanket "Keweenawan Supergroup and Midcontinent Rift Intrusive
# Supersuite" phrase, so the rift-intrusion catch-alls would otherwise
# swallow them.
OVERRIDE_RULES = [
    ("hinckley", "kwsed"),
    ("fond du lac", "kwsed"),
    ("solar church", "kwsed"),
    ("solor church", "kwsed"),
    ("bayfield", "kwsed"),
    ("orienta", "kwsed"),
    ("devil's island", "kwsed"),
    ("chequamegon", "kwsed"),
    ("puckwunge", "kwsed"),
    ("nopeming", "kwsed"),
    ("interflow sandstone", "kwsed"),
    ("chengwatana", "nsvg"),
]

# Classification rules applied against the source map's own assignment.
# Checked in order; first match wins. Keyed on substrings of ``comments``.
COMMENT_RULES = [
    ("duluth complex - anorthositic series", "dc_anorth"),
    ("duluth complex - layered series", "dc_layered"),
    ("duluth complex - felsic series", "dc_felsic"),
    ("beaver bay complex", "bbc"),
    ("north shore volcanic group", "nsvg"),
    ("miscellaneous intrusions", "mcr_intr"),
    # Catch-all for rift intrusions not assigned to a named complex; must come
    # AFTER the Duluth Complex / Beaver Bay Complex rules, whose comments also
    # carry the "Midcontinent Rift Intrusive Supersuite" phrase.
    ("midcontinent rift intrusive supersuite", "mcr_intr"),
    ("keweenawan", "mcr_intr"),
    ("animikie group", "animikie"),
    ("penokean orogen", "paleoprot"),
    ("superior province", "archean"),
    ("wawa and wabigoon subprovinces", "archean"),
    ("quetico subprovince", "archean"),
]

# Some units carry the grouping only in strat_name.
STRAT_RULES = [
    ("beaver bay complex", "bbc"),
    ("duluth complex", "dc_layered"),
    ("north shore volcanic group", "nsvg"),
    ("biwabik", "animikie"),
    ("virginia", "animikie"),
    ("giants range", "archean"),
]

# Last-resort rules on the unit name, for polygons with neither field populated.
# The "volcanic" rule catches the map's "Undifferentiated volcanic rocks and
# volcanic hornfels" (1600-1000 Ma) at the Duluth Complex roof; Archean
# volcanic units never reach it because classify() assigns them by age first.
NAME_RULES = [
    ("iron formation", "paleoprot"),
    ("iron-formation", "paleoprot"),
    ("graywacke", "animikie"),
    ("slate", "animikie"),
    ("granophyre", "mcr_intr"),
    ("volcanic", "nsvg"),
]


def classify(props):
    """Assign a map unit to a display group using the source map's own grouping.

    Args:
        props: The ``properties`` dict of a Macrostrat map polygon.

    Returns:
        A key into UNIT_GROUPS, or None if the unit could not be classified.
    """
    comments = (props.get("comments") or "").lower()
    strat = (props.get("strat_name") or "").lower()
    name = (props.get("name") or "").lower()

    b_age = props.get("b_age")
    if b_age is not None and b_age < 541:
        return "phanerozoic"

    for key, group in OVERRIDE_RULES:
        if key in strat or key in name:
            return group

    for key, group in COMMENT_RULES:
        if key in comments:
            return group
    for key, group in STRAT_RULES:
        if key in strat:
            return group

    # Several state-map units in this area (greenstone-belt volcanics,
    # "Magnetic intrusions, undifferentiated") carry no grouping in comments or
    # strat_name; their Archean age assignment is unambiguous, so classify on
    # age before falling back to the name rules.
    t_age = props.get("t_age")
    if t_age is not None and t_age >= 2450:
        return "archean"

    for key, group in NAME_RULES:
        if key in name:
            return group
    return None


# Simplification tolerance, degrees (~50 m at this latitude): far finer than
# the 1:500k source linework, but cuts the vertex count enough to keep the
# standalone HTML responsive with four counties of polygons embedded in it.
SIMPLIFY_TOL = 0.0005


def _round_coords(geom_mapping, ndigits=5):
    """Round the coordinates of a GeoJSON geometry mapping in place-ish.

    Five decimal places (~1 m) is well below display resolution; trimming the
    default 15-digit floats roughly halves the size of the embedded GeoJSON.

    Args:
        geom_mapping: A GeoJSON-style geometry dict from shapely.mapping.
        ndigits: Decimal places to keep.

    Returns:
        The geometry dict with rounded coordinates.
    """
    def rnd(obj):
        if isinstance(obj, (list, tuple)):
            return [rnd(x) for x in obj]
        if isinstance(obj, float):
            return round(obj, ndigits)
        return obj

    out = dict(geom_mapping)
    out["coordinates"] = rnd(out["coordinates"])
    return out


def build_geology_layer(features, lake=None):
    """Build the geology GeoJson overlay and record which groups appear.

    Args:
        features: List of Macrostrat GeoJSON feature dicts.
        lake: Optional shapely geometry (lon/lat) to clip the polygons
            against, so that geology mapped beneath Lake Superior ends at
            the shoreline.

    Returns:
        Tuple of (folium.GeoJson layer, list of group keys present, in
        UNIT_GROUPS order).
    """
    lake_hits = prep(lake).intersects if lake is not None else lambda g: False
    present = set()
    unclassified = set()
    out_features = []
    for feat in features:
        props = feat["properties"]
        name = props.get("name", "")
        if not name or name == "water":
            continue  # lakes show through from the base map
        group = classify(props)
        if group is None:
            unclassified.add(name)
            color, label = CLR_DEFAULT, "Unclassified"
        else:
            present.add(group)
            color, label = UNIT_GROUPS[group]
        geom = shape(feat["geometry"]).simplify(
            SIMPLIFY_TOL, preserve_topology=True)
        if lake_hits(geom):
            geom = geom.difference(lake)
        if geom.is_empty:
            continue
        b_age, t_age = props.get("b_age"), props.get("t_age")
        age = (f"{b_age:g}–{t_age:g} Ma"
               if b_age is not None and t_age is not None else "n/a")
        out_features.append({
            "type": "Feature",
            "geometry": _round_coords(mapping(geom)),
            "properties": {
                "unit": name,
                "group": label,
                "strat_name": props.get("strat_name") or "-",
                "lith": props.get("lith") or "-",
                "age": age,
                "fill": color,
            },
        })
    for n in sorted(unclassified):
        print(f"  WARNING: unclassified unit -> {n!r}")

    layer = folium.GeoJson(
        {"type": "FeatureCollection", "features": out_features},
        name="Bedrock geology (Macrostrat)",
        style_function=lambda f: {
            "fillColor": f["properties"]["fill"],
            "fillOpacity": 0.75,
            "color": "#555555",
            "weight": 0.7,
        },
        highlight_function=lambda f: {"fillOpacity": 0.9, "weight": 2},
        tooltip=folium.GeoJsonTooltip(
            fields=["unit", "group", "age"],
            aliases=["Unit", "Group", "Age"],
        ),
        popup=folium.GeoJsonPopup(
            fields=["unit", "group", "strat_name", "lith", "age"],
            aliases=["Unit", "Group", "Strat name", "Lithology", "Age"],
            max_width=350,
        ),
    )
    ordered = [g for g in UNIT_GROUPS if g in present]
    return layer, ordered


def legend_html(groups_present):
    """Build a fixed-position HTML legend for the unit groups on the map.

    Args:
        groups_present: List of UNIT_GROUPS keys to include, already ordered.

    Returns:
        HTML string for embedding in the map document.
    """
    rows = "".join(
        f'<div style="margin:2px 0;">'
        f'<span style="display:inline-block;width:14px;height:14px;'
        f'background:{UNIT_GROUPS[g][0]};border:1px solid #555;'
        f'vertical-align:middle;margin-right:6px;"></span>'
        f'<span style="vertical-align:middle;">{UNIT_GROUPS[g][1]}</span></div>'
        for g in groups_present
    )
    return (
        '<div style="position:fixed;bottom:20px;left:10px;z-index:9999;'
        'background:rgba(255,255,255,0.92);padding:8px 12px;'
        'border:1px solid #999;border-radius:4px;'
        'font:12px/1.35 Arial,sans-serif;max-width:280px;">'
        '<b>Bedrock geology</b><br>'
        '<span style="font-size:10px;color:#555;">Macrostrat / MGS state map '
        '(CC-BY 4.0)</span>'
        f'{rows}</div>'
    )


def build_map(lat: float, lon: float, info: dict) -> folium.Map:
    """Build a folium map centered on the drill hole over Macrostrat geology.

    Args:
        lat: Collar latitude in decimal degrees (WGS84).
        lon: Collar longitude in decimal degrees (WGS84).
        info: Metadata dictionary used to populate the marker popup.

    Returns:
        A folium.Map with the classified geology overlay, a legend, selectable
        base layers, and a marker at the collar location.
    """
    fmap = folium.Map(
        location=[lat, lon], zoom_start=9, control_scale=True, tiles=None,
    )

    # Base layers: a muted default so the geology reads clearly, plus
    # imagery/topo for context (no API key required). Leaflet displays the
    # base layer added LAST, so the muted default goes at the end.
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(fmap)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics",
        name="Esri World Imagery (satellite)",
    ).add_to(fmap)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, USGS, NOAA",
        name="Esri World Topographic",
    ).add_to(fmap)
    folium.TileLayer("CartoDB positron", name="CartoDB Positron (muted)").add_to(fmap)

    # Initial grid at ~0.04 deg spacing; gap probing at 0.01 deg. Coarser than
    # the field-guide maps because the 1:500k state map units across four
    # counties are broad -- units narrower than ~1 km may still be missed.
    region = load_county_region()
    lon_min, lat_min, lon_max, lat_max = region.bounds
    features = fetch_macrostrat_polygons(
        lon_range=(lon_min, lon_max),
        lat_range=(lat_min, lat_max),
        cache_path=CACHE_PATH,
        n_lon=int((lon_max - lon_min) / 0.04) + 1,
        n_lat=int((lat_max - lat_min) / 0.04) + 1,
        scale="medium",
        gap_spacing=0.01,
        region=region,
    )
    geology, present = build_geology_layer(features, lake=load_lake())
    geology.add_to(fmap)
    fmap.get_root().html.add_child(folium.Element(legend_html(present)))

    popup_html = (
        f"<b>{info['name']}</b> (DNRNUM {info['dnrnum']})<br>"
        f"{info['area']}<br>"
        f"{info['county']}<br>"
        f"Lat, Lon: {lat:.6f}, {lon:.6f}<br>"
        f"Collar elevation: {info['elev_ft_log']} ft (log) / "
        f"{info['elev_ft_dnr']} ft (DNR)<br>"
        f"End of hole: {info['eoh_ft']} ft<br>"
        f"Orientation: {info['orientation']}"
    )
    folium.Marker(
        location=[lat, lon],
        tooltip=info["name"],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="red", icon="record", prefix="glyphicon"),
    ).add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=None,
        help="output HTML path (default: D-6A_location_map.html next to this script)",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    output = args.output or here / "D-6A_location_map.html"

    fmap = build_map(D6A_LAT, D6A_LON, D6A_INFO)
    fmap.save(str(output))
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
