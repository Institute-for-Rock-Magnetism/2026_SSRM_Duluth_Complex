"""Plot the D-6A drill log section with geochemistry panels using pystrat.

Drill hole D-6A (Dunka Pit area, South Kawishiwi intrusion, Duluth Complex).
Logged by M. Severson, 1992. Three nested geochem datasets bound with the log
(Exxon 1979 assays, DNR 255-1/265/266 PGE package, ICP-MS/XRF thin-section data).

Usage:
    python plot_D_6A.py                   # uses primary intervals (default)
    python plot_D_6A.py --detailed        # uses detailed split-at-every-litho CSV
    python plot_D_6A.py --output myfig    # write to myfig.png and myfig.pdf
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import pystrat

EOH_FT = 2125.0  # End of hole — set y-axis limits to this

# Caption defining the SKTS stratigraphic-unit abbreviations used in the
# FORMATION column (after Severson 1993 Plate III, "South Stratigraphic Line").
UNIT_CAPTION = (
    "Stratigraphic units (after Severson 1993): "
    "MAIN AGT = main augite troctolite; LOW AGT = lower augite troctolite; "
    "UW = Updip Wedge (sulfide-bearing); U1/U2/U3 = Ultramafic One/Two/Three "
    "(interbedded ultramafics + troctolites); BH-U / BH-L = Basal Heterogeneous "
    "(upper/lower); PEG = Pegmatitic Unit of Foose; BAN = Bottom Augite "
    "troctolite to Norite; GRAN = Giants Range granitic footwall."
)


def load_section(section_csv: Path, style_csv: Path):
    """Build pystrat.Section and pystrat.Style from the CSV inputs.

    Section CSV is ordered top-down (overburden first, EOH last) to match the
    original drill log. pystrat treats the first row as the BASE of the section
    and stacks upward, so internal pystrat heights run from 0 at the OVB row to
    EOH at the bottom row. We display with ax.invert_yaxis() so depth increases
    downward in the figure.
    """
    section_df = pd.read_csv(section_csv)
    style_df = pd.read_csv(style_csv)

    # Build Section. units = (GROUP, FORMATION) for hierarchical labels.
    section = pystrat.Section(
        section_df["THICKNESS"].values,
        section_df["FACIES"].values,
        units=section_df[["GROUP", "FORMATION"]].values,
        name="D-6A",
    )

    # Build Style. Colors must be 0-1 RGB tuples for matplotlib.
    colors = (style_df[["R", "G", "B"]].values / 255.0).tolist()
    style = pystrat.Style(
        labels=style_df["facies"].values,
        color_values=colors,
        width_values=style_df["width"].values,
    )
    return section, style, section_df


def attach_geochem(section, geochem_csvs: dict[str, Path]):
    """Attach available geochem CSVs to the Section as data attributes.

    Each entry in geochem_csvs is a {short_name: (csv_path, value_column)}.
    Heights are computed from DEPTH_MID_FT using the same convention as the
    section: pystrat height = DEPTH_MID_FT (because rows are ordered top-down,
    so the OVB row sits at pystrat-height 0).
    """
    for attr_name, (path, col) in geochem_csvs.items():
        if not path.exists():
            print(f"  skipping {attr_name}: {path.name} not found")
            continue
        df = pd.read_csv(path)
        if col not in df.columns:
            print(f"  skipping {attr_name}: column {col!r} not in {path.name}")
            continue
        # Filter to numeric, positive (i.e. above detection — we store BDLs as
        # negative numbers in the CSV; see README).
        values = pd.to_numeric(df[col], errors="coerce")
        mask = values.notna() & (values > 0)
        if not mask.any():
            print(f"  skipping {attr_name}: no above-detection values in {col}")
            continue
        section.add_data_attribute(
            attr_name,
            df["DEPTH_MID_FT"][mask].values,
            values[mask].values,
        )
        print(f"  attached {attr_name}: {mask.sum()} samples from {path.name}")


def build_facies_legend(style, used_facies):
    """Return matplotlib legend Patch handles for every facies present in the section.

    Restricted to facies that actually appear so the legend doesn't clutter
    with unused entries.
    """
    facies_meanings = {
        "OVB":     "Overburden",
        "AT":      "AT — anorthositic troctolite",
        "AAT":     "AAT — anorthositic augite troctolite",
        "AT_T":    "AT/T — anorth. troctolite to troctolite",
        "T":       "T — troctolite",
        "T_ORT":   "T-ORT — troctolite with oxide",
        "T_NOR":   "T-NOR — troctolite to norite",
        "AGT_OG":  "AGT-OG — augite troct. to olivine gabbro",
        "AGT":     "AGT — augite troctolite",
        "GA":      "GA — gabbro",
        "MELAGAB": "MELAGAB — melagabbro",
        "GA_A":    "GA-A — gabbroic anorthosite (altered)",
        "ORT":     "ORT — olivine-rich (oxide) troctolite",
        "PIC":     "PIC — picrite (melatroctolite)",
        "FP":      "FP — feldspathic peridotite",
        "PER":     "PER — peridotite",
        "DUN":     "DUN — dunite",
        "HBLD":    "HBLD — hornblendite",
        "HNFL":    "HNFL — hornfels",
        "HET":     "HET — heterogeneous mixture",
        "PEG":     "PEG — pegmatite",
        "GRANO":   "GRANO — granophyre",
        "QMONZ":   "QMONZ — quartz monzonite (footwall)",
    }
    handles = []
    # iterate in the style file's order so the legend mirrors the palette order
    for label, color in zip(style.labels, style.color_values):
        if label not in used_facies:
            continue
        handles.append(Patch(
            facecolor=color, edgecolor="k", linewidth=0.5,
            label=facies_meanings.get(label, label),
        ))
    return handles


def plot_figure(section, style, geochem_attrs, output_stem: Path):
    """Build the multi-panel figure: section column + geochem panels + legend."""
    n_geochem = len(geochem_attrs)
    # Extra column for the legend.
    n_panels = 1 + n_geochem + 1
    width_ratios = [1.5] + [1.0] * n_geochem + [1.4]
    fig, axes = plt.subplots(
        1, n_panels,
        figsize=(2.5 + 1.6 * n_geochem + 2.2, 13),
        gridspec_kw={"width_ratios": width_ratios, "wspace": 0.08},
    )
    ax_strat = axes[0]
    ax_legend = axes[-1]
    ax_geochem = axes[1:-1]

    # Share y-axis between strat + geochem panels (but not the legend pane).
    for ax in ax_geochem:
        ax.sharey(ax_strat)

    # Lithology column.
    section.plot(
        style,
        ax=ax_strat,
        label_units=True,
        unit_label_wid_tot=0.3,
        unit_fontsize=7,
        xticks=False,
    )
    ax_strat.set_xlim(-0.3, 1)
    ax_strat.set_ylim(0, EOH_FT)
    ax_strat.set_ylabel("Depth from collar (ft)")
    ax_strat.set_title("Lithology", fontsize=10)

    # Geochem panels.
    for ax, (attr_name, label, log_x) in zip(ax_geochem, geochem_attrs):
        if not hasattr(section, attr_name):
            ax.text(0.5, 0.5, f"no data\n({attr_name})", ha="center", va="center",
                    transform=ax.transAxes, fontsize=8, color="0.5")
            ax.set_xticks([])
            ax.set_yticks([])
            continue
        data = getattr(section, attr_name)
        ax.plot(data.values, data.height, "o", markersize=3,
                color="C0", clip_on=False)
        ax.set_xlabel(label)
        if log_x:
            ax.set_xscale("log")
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_axisbelow(True)
        # Hide y-tick labels on the inner panels — the strat axis carries them.
        ax.tick_params(labelleft=False)

    # Make depth go down on the y-axis (drill core convention).
    for ax in [ax_strat, *ax_geochem]:
        ax.set_ylim(0, EOH_FT)
        ax.invert_yaxis()

    # Legend panel.
    used_facies = set(section.facies)
    handles = build_facies_legend(style, used_facies)
    ax_legend.axis("off")
    ax_legend.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(-0.05, 1),
        frameon=False,
        fontsize=8,
        handlelength=1.4,
        handleheight=1.1,
        labelspacing=0.55,
        title="Facies",
        title_fontsize=9,
    )

    fig.suptitle(
        "D-6A — Severson 1992 — South Kawishiwi intrusion, Dunka Pit",
        y=0.995, fontsize=12, fontweight="bold",
    )
    # Multi-line caption under the suptitle.
    fig.text(
        0.5, 0.965, UNIT_CAPTION,
        ha="center", va="top", fontsize=8, color="0.25",
        wrap=True,
    )

    fig.tight_layout(rect=(0, 0, 1, 0.945))

    png_path = output_stem.with_suffix(".png")
    pdf_path = output_stem.with_suffix(".pdf")
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    print(f"\nwrote {png_path}")
    print(f"wrote {pdf_path}")
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--detailed", action="store_true",
        help="use the detailed section CSV (137 rows; split at every lithologic "
             "change) instead of the primary intervals (42 rows)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="output file stem (without extension). Default: D_6A_section_<primary|detailed>",
    )
    parser.add_argument(
        "--show", action="store_true",
        help="show the figure interactively in addition to saving",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent

    section_csv = here / (
        "D_6A_section_detailed.csv" if args.detailed else "D_6A_section_primary.csv"
    )
    style_csv = here / "D_6A_style.csv"

    if args.output is None:
        args.output = here / (
            "D_6A_plot_detailed" if args.detailed else "D_6A_plot_primary"
        )

    print(f"section: {section_csv.name}")
    print(f"style:   {style_csv.name}")

    section, style, _ = load_section(section_csv, style_csv)
    print(f"  {section.n_beds} beds, {section.total_thickness:.0f} ft total")
    print(f"  {section.n_unique_facies} unique facies")

    # Wire up the Exxon 1979 geochem dataset only. (attribute_name, csv_filename, value_column).
    print("\ngeochem:")
    attach_geochem(section, {
        "Cu_pct": (here / "D_6A_geochem_exxon.csv", "Cu_pct"),
        "Ni_ppm": (here / "D_6A_geochem_exxon.csv", "Ni_ppm"),
        "Co_ppm": (here / "D_6A_geochem_exxon.csv", "Co_ppm"),
    })

    # (attribute_name, x-axis label, log_x?)
    panels = [
        ("Cu_pct", "Cu (wt%)", True),
        ("Ni_ppm", "Ni (ppm)", True),
        ("Co_ppm", "Co (ppm)", False),
    ]

    plot_figure(section, style, panels, args.output)

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
