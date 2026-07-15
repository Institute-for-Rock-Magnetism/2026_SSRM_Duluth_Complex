"""Fetch geologic map polygons from the Macrostrat API and cache locally.

The Macrostrat map endpoint is queried by POINT (there is no bounding-box or
WKT-shape parameter), so a map area has to be discovered by sampling. A plain
coarse grid misses any polygon narrower than the grid spacing, which leaves
holes in the rendered map. Along the North Shore these showed up as pale gaps
running through the middle of the North Shore Volcanic Group and the Beaver Bay
Complex, because the mapped units there are long and thin -- the gaps looked
like a distinct grey map unit, but they were simply missing data.

This module therefore samples ADAPTIVELY: it starts from a coarse grid, then
repeatedly finds the parts of the bounding box not yet covered by any returned
polygon and queries only there, until coverage converges. Queries run
concurrently, so this stays fast despite the number of requests.

Usage
-----
    from fetch_macrostrat import fetch_macrostrat_polygons

    features = fetch_macrostrat_polygons(
        lon_range=(-92.0, -91.0),
        lat_range=(46.2, 46.7),
        cache_path=Path("macrostrat_polygons.json"),
        scale="medium",
    )

Each feature is a GeoJSON dict with geometry and properties including
``name``, ``strat_name``, ``lith``, ``comments``, ``color``, ``t_age``, etc.

API reference: https://macrostrat.org/api/v2
Data licence : CC-BY 4.0
"""

import json
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

import numpy as np

# Prefer IPv4 when connecting. urllib tries addresses in getaddrinfo order and
# waits out a full TCP timeout (~30 s) on each; on networks where the IPv6
# route to macrostrat.org is broken, that turns every sub-second query into a
# 30-second one. Sorting IPv4 first avoids the dead route without changing
# behavior anywhere IPv6 works.
_getaddrinfo = socket.getaddrinfo


def _ipv4_first(*args, **kwargs):
    infos = _getaddrinfo(*args, **kwargs)
    return sorted(infos, key=lambda info: info[0] != socket.AF_INET)


socket.getaddrinfo = _ipv4_first
from shapely.geometry import Point, box, shape
from shapely.ops import unary_union
from shapely.prepared import prep


def _query_point(lat, lon, scale):
    """Query Macrostrat for the map polygons at a single point.

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.
        scale: Macrostrat map scale ('tiny', 'small', 'medium', 'large').

    Returns:
        List of GeoJSON feature dicts (may be empty).
    """
    url = (
        f"https://macrostrat.org/api/v2/geologic_units/map"
        f"?lat={lat:.5f}&lng={lon:.5f}&format=geojson&scale={scale}"
    )
    try:
        data = json.loads(urlopen(url, timeout=30).read())
        return data["success"]["data"]["features"]
    except Exception as exc:  # noqa: BLE001 - network errors are expected here
        print(f"  Warning: query at ({lat:.3f}, {lon:.3f}) failed: {exc}")
        return []


def _sample(points, scale, seen, workers=12):
    """Query a batch of points concurrently, adding new polygons to ``seen``.

    Args:
        points: Iterable of (lat, lon) tuples.
        scale: Macrostrat map scale.
        seen: Dict of map_id -> feature, mutated in place.
        workers: Number of concurrent requests.

    Returns:
        Number of newly discovered polygons.
    """
    before = len(seen)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for feats in pool.map(lambda p: _query_point(p[0], p[1], scale), points):
            for feat in feats:
                seen.setdefault(feat["properties"]["map_id"], feat)
    return len(seen) - before


def fetch_macrostrat_polygons(
    lon_range,
    lat_range,
    cache_path,
    n_lon=24,
    n_lat=18,
    scale="medium",
    max_rounds=6,
    gap_spacing=0.004,
    region=None,
):
    """Query Macrostrat geologic map polygons over a bounding box or region.

    Samples a coarse grid first, then iteratively queries the uncovered parts of
    the box until no significant gaps remain. The gap-filling matters because
    the endpoint only accepts point queries, and a fixed grid silently drops any
    map unit narrower than the grid spacing.

    Args:
        lon_range: (min_lon, max_lon) in decimal degrees.
        lat_range: (min_lat, max_lat) in decimal degrees.
        cache_path: Path to a JSON file for caching results.
        n_lon: Number of longitude points in the initial coarse grid.
        n_lat: Number of latitude points in the initial coarse grid.
        scale: Macrostrat map scale -- 'tiny', 'small', 'medium', or 'large'.
        max_rounds: Maximum number of gap-filling rounds.
        gap_spacing: Spacing, in degrees, of the grid used to detect gaps. This
            sets the size of the smallest hole that will be chased down.
        region: Optional shapely geometry (lon/lat). If given, sampling and
            gap-probing are restricted to points inside it, so an irregular
            area (e.g. a group of counties) can be fetched without wasting
            thousands of queries on the unmapped parts of its bounding box.

    Returns:
        List of GeoJSON feature dicts, one per unique map polygon.
    """
    cache_path = Path(cache_path)
    if cache_path.exists():
        print(f"Loading cached polygons from {cache_path.name}")
        with open(cache_path) as fh:
            return json.load(fh)

    print(f"Fetching geologic map polygons from Macrostrat ({scale} scale)...")
    seen = {}
    in_region = prep(region).contains if region is not None else lambda pt: True

    # Round 0: coarse grid over the whole box (clipped to the region if given).
    lons = np.linspace(lon_range[0], lon_range[1], n_lon)
    lats = np.linspace(lat_range[0], lat_range[1], n_lat)
    grid = [(la, lo) for la in lats for lo in lons if in_region(Point(lo, la))]
    _sample(grid, scale, seen)
    print(f"  initial grid: {len(grid)} points, {len(seen)} polygons")

    # Rounds 1..N: find points in the box that no polygon covers, and query only
    # those. Narrow units missed by the coarse grid get picked up here.
    bbox = box(lon_range[0], lat_range[0], lon_range[1], lat_range[1])
    if region is not None:
        bbox = bbox.intersection(region)
    probes = [
        (la, lo)
        for la in np.arange(lat_range[0], lat_range[1], gap_spacing)
        for lo in np.arange(lon_range[0], lon_range[1], gap_spacing)
        if in_region(Point(lo, la))
    ]

    for rnd in range(1, max_rounds + 1):
        covered = unary_union(
            [shape(f["geometry"]).buffer(0) for f in seen.values()]
        ).intersection(bbox)
        ready = prep(covered)
        gaps = [(la, lo) for la, lo in probes if not ready.contains(Point(lo, la))]
        if not gaps:
            print(f"  round {rnd}: no gaps remain")
            break
        found = _sample(gaps, scale, seen)
        print(f"  round {rnd}: probed {len(gaps)} uncovered points, "
              f"found {found} new polygons ({len(seen)} total)")
        if found == 0:
            # Remaining gaps are genuinely unmapped (e.g. open water beyond the
            # map's extent), not holes in coverage.
            break

    features = list(seen.values())
    print(f"  {len(features)} unique geologic map polygons")

    with open(cache_path, "w") as fh:
        json.dump(features, fh)
    print(f"  cached to {cache_path.name}")
    return features
