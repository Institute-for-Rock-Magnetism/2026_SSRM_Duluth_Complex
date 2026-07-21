#!/usr/bin/env python
"""Convert the D6A-BAN CIT-format demagnetization data to MagIC format.

This script reads the CIT files in this directory (the ``D6A-BAN.sam`` site
file and the per-sample demagnetization files it references) and writes the
five MagIC tables (specimens, samples, sites, locations, measurements) into
``D-6A_data/RAPID_SRM/MagIC_format/D6A-BAN``.

The conversion parameters are read from the ``D6A-BAN.inp`` file that sits
alongside the data, so this script stays in sync with the RAPID SRM pipeline
that produced it. The ``.inp`` file is a three-line, tab-delimited file:

    CIT
    sam_path<tab>field_magic_codes<tab>location<tab>naming_convention<tab>...
    ./D6A-BAN.sam<tab>SO-V<tab>D6A-BAN<tab>2<tab>1<tab>True<tab>None<tab>0.0

Run it from anywhere with the ``rockmag`` environment active:

    python convert_to_magic.py

The heavy lifting is done by ``pmagpy.convert_2_magic.cit``; this script only
locates the files, translates the ``.inp`` fields into that function's
arguments, and reports what was written.
"""

from pathlib import Path

from pmagpy import convert_2_magic as convert

# This script lives in the CIT data directory; outputs go to the parallel
# MagIC_format tree. Paths are resolved relative to the script so it can be
# run from any working directory.
INPUT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = INPUT_DIR.parents[1] / "MagIC_format" / INPUT_DIR.name
INP_FILE = INPUT_DIR / "D6A-BAN.inp"


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


def main():
    """Run the CIT-to-MagIC conversion for D6A-BAN."""
    params = read_inp(INP_FILE)

    # Translate the .inp fields into convert.cit() arguments. The sam_path in
    # the .inp is relative to the input directory; only its file name is
    # needed because input_dir_path locates it.
    magfile = Path(params["sam_path"]).name
    methods = params["field_magic_codes"].split(":")
    samp_con = params["naming_convention"]
    specnum = int(params["num_terminal_char"])
    noave = params["dont_average_replicate_measurements"].strip() == "True"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Input : {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Parameters from {INP_FILE.name}: magfile={magfile}, "
          f"location={params['location']}, methods={methods}, "
          f"samp_con={samp_con}, specnum={specnum}, noave={noave}\n")

    success, meas_file = convert.cit(
        dir_path=str(OUTPUT_DIR),
        input_dir_path=str(INPUT_DIR),
        magfile=magfile,
        locname=params["location"],
        methods=methods,
        samp_con=samp_con,
        specnum=specnum,
        noave=noave,
    )

    if not success:
        raise RuntimeError("convert.cit reported a failure; see messages above")

    written = ["specimens.txt", "samples.txt", "sites.txt",
               "locations.txt", meas_file]
    print("\nWrote MagIC tables to", OUTPUT_DIR)
    for name in written:
        print("  ", name)


if __name__ == "__main__":
    main()
