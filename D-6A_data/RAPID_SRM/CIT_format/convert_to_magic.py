#!/usr/bin/env python
"""Convert every RAPID SRM CIT-format locality to MagIC format.

This is the single entry point for the RAPID SRM CIT -> MagIC conversion. It
discovers every locality folder in this directory -- each holds a
``<locality>.sam`` site file, the per-sample demagnetization files it
references, and a ``<locality>.inp`` parameter file -- and for each one:

1. runs ``pmagpy.convert_2_magic.cit`` to write the five MagIC tables
   (specimens, samples, sites, locations, measurements) into
   ``../MagIC_format/<locality>/``, then
2. adds mass/volume normalization via :mod:`rapid_normalize` (specimen
   ``weight`` and ``volume``; measurement ``magn_mass`` and ``magn_volume``).

The ``.inp`` file is a three-line, tab-delimited file, e.g.::

    CIT
    sam_path<tab>field_magic_codes<tab>location<tab>naming_convention<tab>...
    ./D6A-BAN.sam<tab>SO-V<tab>D6A-BAN<tab>5<tab>1<tab>True<tab>None<tab>0.0

Run from anywhere with the ``rockmag`` environment active::

    python convert_to_magic.py            # all localities
    python convert_to_magic.py D6A-BAN D6A-BH   # only the named localities
"""

import sys
from collections import Counter
from pathlib import Path

# This script and rapid_normalize.py live together in CIT_format/; make the
# import work regardless of the current working directory.
CIT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(CIT_ROOT))

from pmagpy import convert_2_magic as convert
from pmagpy import pmag

from rapid_normalize import load_masses, add_normalizations

MAGIC_ROOT = CIT_ROOT.parent / "MagIC_format"

# In addition to the per-locality folders, all localities are merged into this
# one folder so the whole RAPID SRM dataset can be viewed or uploaded together.
COMBINED_NAME = "D6A-all"
MAGIC_TABLES = ["specimens", "samples", "sites", "locations", "measurements"]
# primary-key column per table, used to check for name collisions when merging
PRIMARY_KEY = {"specimens": "specimen", "samples": "sample", "sites": "site",
               "locations": "location", "measurements": "measurement"}


def read_inp(inp_path):
    """Read a CIT ``.inp`` parameter file into a dictionary.

    Args:
        inp_path (Path): Path to the ``.inp`` file. The first line is the
            format marker (``CIT``); the second line holds tab-delimited
            column names; the third line holds the matching values.

    Returns:
        dict: Parameter name mapped to its string value.
    """
    lines = inp_path.read_text().splitlines()
    if not lines or lines[0].strip() != "CIT":
        raise ValueError(f"{inp_path} does not look like a CIT .inp file")
    keys = lines[1].split("\t")
    values = lines[2].split("\t")
    return dict(zip(keys, values))


def find_localities(only=None):
    """Find locality folders that contain a matching ``.inp`` file.

    Args:
        only (set or None): If given, restrict to these locality (folder)
            names.

    Returns:
        list[Path]: The ``<locality>.inp`` path for each locality, sorted by
        name.
    """
    inps = []
    for sub in sorted(CIT_ROOT.iterdir()):
        if not sub.is_dir():
            continue
        if only and sub.name not in only:
            continue
        inp = sub / f"{sub.name}.inp"
        if inp.exists():
            inps.append(inp)
    return inps


def convert_locality(inp_path, masses):
    """Convert one locality to MagIC format and add normalization.

    Args:
        inp_path (Path): The locality's ``.inp`` file.
        masses (dict): ``specimen`` -> mass in grams, from
            :func:`rapid_normalize.load_masses`.

    Returns:
        dict: The counts returned by
        :func:`rapid_normalize.add_normalizations`.
    """
    input_dir = inp_path.parent
    output_dir = MAGIC_ROOT / input_dir.name
    params = read_inp(inp_path)

    # Translate the .inp fields into convert.cit() arguments. The sam_path is
    # relative to the input directory; only its file name is needed because
    # input_dir_path locates it.
    magfile = Path(params["sam_path"]).name
    methods = params["field_magic_codes"].split(":")
    samp_con = params["naming_convention"]
    specnum = int(params["num_terminal_char"])
    noave = params["dont_average_replicate_measurements"].strip() == "True"

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[{input_dir.name}] magfile={magfile}, location={params['location']}, "
          f"methods={methods}, samp_con={samp_con}, specnum={specnum}, noave={noave}")

    success, _ = convert.cit(
        dir_path=str(output_dir),
        input_dir_path=str(input_dir),
        magfile=magfile,
        locname=params["location"],
        methods=methods,
        samp_con=samp_con,
        specnum=specnum,
        noave=noave,
    )
    if not success:
        raise RuntimeError(
            f"convert.cit failed for {input_dir.name}; see messages above")

    return add_normalizations(output_dir, masses)


def combine_localities():
    """Merge every converted locality into one combined MagIC table set.

    Reads the per-locality MagIC tables already written under ``MagIC_format``
    and concatenates them into ``MagIC_format/<COMBINED_NAME>/``. The
    ``measurements`` ``sequence`` column is renumbered across the whole set, and
    a warning is printed if any table has colliding primary keys (which would
    make the combined contribution invalid).

    Returns:
        tuple[Path, dict]: The combined folder and a table -> record-count map.
    """
    combined_dir = MAGIC_ROOT / COMBINED_NAME
    combined_dir.mkdir(parents=True, exist_ok=True)
    locality_dirs = [MAGIC_ROOT / inp.parent.name for inp in find_localities()]

    summary = {}
    for table in MAGIC_TABLES:
        recs = []
        for loc_dir in locality_dirs:
            table_file = loc_dir / f"{table}.txt"
            if table_file.exists():
                data, _ = pmag.magic_read(str(table_file))
                recs.extend(data)
        if not recs:
            continue

        if table == "measurements":
            for i, rec in enumerate(recs):
                rec["sequence"] = str(i)

        key = PRIMARY_KEY[table]
        dups = [v for v, n in Counter(r.get(key, "") for r in recs).items()
                if v and n > 1]
        if dups:
            print(f"    WARNING: {table} has {len(dups)} duplicate '{key}' "
                  f"across localities, e.g. {sorted(dups)[:5]}")

        pmag.magic_write(str(combined_dir / f"{table}.txt"), recs, table)
        summary[table] = len(recs)
    return combined_dir, summary


def main(argv=None):
    """Convert all localities (or only those named on the command line)."""
    only = set(argv) if argv else None
    inps = find_localities(only)
    if not inps:
        raise SystemExit("No locality .inp files found to convert.")

    masses = load_masses()
    for inp_path in inps:
        counts = convert_locality(inp_path, masses)
        print(f"    -> weight for {counts['specimens']} specimens; "
              f"magn_mass in {counts['magn_mass']} and magn_volume in "
              f"{counts['magn_volume']} measurements\n")

    print(f"Converted {len(inps)} localit"
          f"{'y' if len(inps) == 1 else 'ies'} into {MAGIC_ROOT}")

    combined_dir, summary = combine_localities()
    print(f"Combined all localities into {combined_dir}:")
    for table, n in summary.items():
        print(f"    {table}: {n}")


if __name__ == "__main__":
    main(sys.argv[1:])
