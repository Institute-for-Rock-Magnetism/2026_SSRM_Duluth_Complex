from __future__ import annotations

import base64
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
VIS_DIR = Path(
    "/Users/penokean/.codex/visualizations/2026/07/14/"
    "019f60fd-0554-7313-95a6-3a4d552b3723"
)
TEMPLATE = VIS_DIR / "aeromagnetic-minnesota.template.html"
OUTPUT = VIS_DIR / "aeromagnetic-minnesota.html"
DATA_DIR = PROJECT / "data" / "aeromagnetic"


def encoded(name: str) -> str:
    return base64.b64encode((DATA_DIR / name).read_bytes()).decode("ascii")


fragment = TEMPLATE.read_text(encoding="utf-8")
replacements = {
    "__TOTAL_IMAGE__": encoded("total-field-vik.jpg"),
    "__TOTAL_SAMPLE_IMAGE__": encoded("total-field.jpg"),
    "__TILT_IMAGE__": encoded("tilt-enhanced-vik.jpg"),
    "__FVD_IMAGE__": encoded("first-vertical-derivative.jpg"),
    "__COLOR_LEGEND__": encoded("vik-legend.png"),
    "__ORIGINAL_COLOR_LEGEND__": encoded("color-legend.png"),
    "__FVD_LEGEND__": encoded("fvd-legend.png"),
}

for placeholder, value in replacements.items():
    fragment = fragment.replace(placeholder, value)

OUTPUT.write_text(fragment, encoding="utf-8")
print(OUTPUT)
