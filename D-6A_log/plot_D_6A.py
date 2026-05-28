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
    "MAIN AGT = main augite troctolite; "
    "UW = Updip Wedge (sulfide-bearing); U1/U2/U3 = Ultramafic One/Two/Three "
    "(interbedded ultramafics + troctolites); BH (u) = upper Basal Heterogeneous, "
    "BH = thin basal interval just above BAN (u); PEG = Pegmatitic Unit of Foose; "
    "BAN (u) / BAN (l) = Bottom "
    "Augite troctolite to Norite, upper/lower (split by the U3 ultramafic unit; "
    "per M. Severson 2026 sampling annotation); GRAN = Giants Range granitic footwall."
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


def load_magnetics_samples(samples_csv: Path) -> pd.DataFrame:
    """Load magnetics sample footages from ../D-6A_sampling/D-6A_samples.csv.

    Returns a DataFrame with a numeric `footage` column. Rows without a
    footage value (the file has placeholder rows for not-yet-described samples)
    are kept — only rows where footage fails to parse are dropped.
    """
    df = pd.read_csv(samples_csv)
    df.columns = [c.strip() for c in df.columns]
    df["footage"] = pd.to_numeric(df["footage"], errors="coerce")
    df = df.dropna(subset=["footage"]).reset_index(drop=True)
    return df


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


def attach_susceptibility(section, csv_path: Path, attr_name: str = "susc"):
    """Attach the KT10 magnetic-susceptibility down-core profile to the Section.

    CSV columns: Depth (ft from collar), Susceptibility (10^-3 SI), Other notes.
    Height = Depth (same top-down convention as the section). Points are sorted
    by depth so the panel can draw a connecting line through the dense profile.
    """
    if not csv_path.exists():
        print(f"  skipping {attr_name}: {csv_path.name} not found")
        return
    df = pd.read_csv(csv_path)
    depth = pd.to_numeric(df["Depth"], errors="coerce")
    susc = pd.to_numeric(df["Susceptibility (10^-3 SI)"], errors="coerce")
    mask = depth.notna() & susc.notna() & (susc > 0)
    if not mask.any():
        print(f"  skipping {attr_name}: no valid values in {csv_path.name}")
        return
    d = depth[mask].values
    s = susc[mask].values
    order = d.argsort()
    section.add_data_attribute(attr_name, d[order], s[order])
    print(f"  attached {attr_name}: {mask.sum()} measurements from {csv_path.name} "
          f"(depth {d.min():.0f}-{d.max():.0f} ft)")


def build_facies_legend(style, used_facies):
    """Return matplotlib legend Patch handles for every facies present in the section.

    Restricted to facies that actually appear so the legend doesn't clutter
    with unused entries.
    """
    facies_meanings = {
        "OVB":     "Overburden",
        "AT":      "AT — anorthositic troctolite",
        "AAT":     "AAT — augite-bearing anorthositic troctolite",
        "AT_T":    "AT/T — anorth. troctolite to troctolite",
        "T":       "T — troctolite",
        "T_ORT":   "T-ORT — troctolite to olivine-rich troctolite",
        "T_NOR":   "T-NOR — troctolite to norite",
        "AGT_OG":  "AGT-OG — augite troct. to olivine gabbro",
        "AGT":     "AGT — augite troctolite",
        "GA":      "GA — gabbroic anorthosite",
        "MELAGAB": "MELAGAB — melagabbro",
        "GA_A":    "GA-A — altered gabbroic anorthosite",
        "ORT":     "ORT — olivine-rich troctolite (40–50% ol)",
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


def plot_samples_panel(ax, samples_df, sharey_ax):
    """Draw horizontal markers + footage labels at each magnetics-sample depth."""
    ax.set_xlim(0, 1)
    ax.sharey(sharey_ax)
    for ft in samples_df["footage"]:
        ax.hlines(ft, xmin=0.0, xmax=0.55, color="#c0392b", linewidth=1.0, alpha=0.9)
        ax.text(0.62, ft, f"{ft:.0f}", ha="left", va="center",
                fontsize=6, color="black")
    ax.set_xticks([])
    ax.tick_params(labelleft=False)
    ax.set_title("Magnetics\nsamples", fontsize=9)
    for spine in ("top", "right", "bottom"):
        ax.spines[spine].set_visible(False)
    ax.text(0.5, -0.015, f"n = {len(samples_df)}",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=7, color="0.35")


def plot_figure(section, style, geochem_attrs, output_stem: Path, samples_df=None):
    """Build the multi-panel figure: section column + samples + geochem panels + legend."""
    n_geochem = len(geochem_attrs)
    has_samples = samples_df is not None and len(samples_df) > 0
    n_samples_col = 1 if has_samples else 0
    # Extra column for the legend.
    n_panels = 1 + n_samples_col + n_geochem + 1
    width_ratios = [1.5] + ([0.45] if has_samples else []) + [1.0] * n_geochem + [1.4]
    fig, axes = plt.subplots(
        1, n_panels,
        figsize=(2.5 + 0.55 * n_samples_col + 1.6 * n_geochem + 2.2, 13),
        gridspec_kw={"width_ratios": width_ratios, "wspace": 0.08},
    )
    ax_strat = axes[0]
    ax_legend = axes[-1]
    if has_samples:
        ax_samples = axes[1]
        ax_geochem = axes[2:-1]
    else:
        ax_samples = None
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

    # Magnetics-samples panel (between strat and geochem).
    if ax_samples is not None:
        plot_samples_panel(ax_samples, samples_df, sharey_ax=ax_strat)

    # Geochem / data panels. Panel tuple: (attr_name, label, log_x, kind).
    for ax, (attr_name, label, log_x, kind) in zip(ax_geochem, geochem_attrs):
        if not hasattr(section, attr_name):
            ax.text(0.5, 0.5, f"no data\n({attr_name})", ha="center", va="center",
                    transform=ax.transAxes, fontsize=8, color="0.5")
            ax.set_xticks([])
            ax.set_yticks([])
            continue
        data = getattr(section, attr_name)
        if kind == "points":
            # Dense profile drawn as small unconnected dots (no implied
            # continuity between discrete measurements).
            ax.plot(data.values, data.height, ".", markersize=1.8,
                    color="C4", clip_on=False, linestyle="none")
        else:
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
    axes_with_depth = [ax_strat, *ax_geochem]
    if ax_samples is not None:
        axes_with_depth.append(ax_samples)
    for ax in axes_with_depth:
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

    # Magnetics-sample footages (sibling D-6A_sampling/ directory).
    samples_csv = here.parent / "D-6A_sampling" / "D-6A_samples.csv"
    if samples_csv.exists():
        samples_df = load_magnetics_samples(samples_csv)
        print(f"\nmagnetics samples: {len(samples_df)} footages from {samples_csv.name}")
    else:
        samples_df = None
        print(f"\nmagnetics samples: {samples_csv} not found — skipping panel")

    # Wire up the Exxon 1979 geochem dataset only. (attribute_name, csv_filename, value_column).
    print("\ngeochem:")
    attach_geochem(section, {
        "Cu_pct": (here / "D_6A_geochem_exxon.csv", "Cu_pct"),
        "Ni_ppm": (here / "D_6A_geochem_exxon.csv", "Ni_ppm"),
        "Co_ppm": (here / "D_6A_geochem_exxon.csv", "Co_ppm"),
    })

    # KT10 magnetic-susceptibility profile (sibling D-6A_data/ directory).
    print("\nsusceptibility:")
    susc_csv = (here.parent / "D-6A_data" / "susceptibility_KT10"
                / "D-6A_KT10_susceptibility.csv")
    attach_susceptibility(section, susc_csv)

    # (attribute_name, x-axis label, log_x?, kind)
    panels = [
        ("Cu_pct", "Cu (wt%)", True, "markers"),
        ("Ni_ppm", "Ni (ppm)", True, "markers"),
        ("Co_ppm", "Co (ppm)", False, "markers"),
        ("susc", "Mag. susc.\n(10$^{-3}$ SI)", True, "points"),
    ]

    plot_figure(section, style, panels, args.output, samples_df=samples_df)

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
