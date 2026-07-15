from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data" / "aeromagnetic"

TICK_VALUES = np.array(
    [
        783, 553, 420, 331, 258, 204, 161, 126, 96, 71, 47, 25, 6,
        -12, -29, -45, -60, -74, -88, -102, -115, -128, -141, -154,
        -167, -180, -193, -206, -220, -233, -247, -262, -277, -295,
        -319, -354, -416, -560,
    ],
    dtype=np.float32,
)
FIRST_TICK_Y = 6.0
LAST_TICK_Y = 457.0


def anomaly_at_y(y: np.ndarray) -> np.ndarray:
    position = np.clip((y - FIRST_TICK_Y) / (LAST_TICK_Y - FIRST_TICK_Y), 0, 1)
    position *= len(TICK_VALUES) - 1
    lower = np.floor(position).astype(np.int16)
    upper = np.minimum(lower + 1, len(TICK_VALUES) - 1)
    fraction = position - lower
    return TICK_VALUES[lower] + (TICK_VALUES[upper] - TICK_VALUES[lower]) * fraction


def vik_index(values: np.ndarray) -> np.ndarray:
    normalized = np.empty_like(values, dtype=np.float32)
    negative = values < 0
    normalized[negative] = 0.5 * (values[negative] + 560.0) / 560.0
    normalized[~negative] = 0.5 + 0.5 * values[~negative] / 783.0
    return np.clip(np.rint(normalized * 255), 0, 255).astype(np.uint8)


legend_image = Image.open(DATA / "color-legend.png").convert("RGB")
legend = np.asarray(legend_image, dtype=np.float32)
legend_y = np.arange(4, 460, dtype=np.int16)
legend_rgb = legend[legend_y, round(legend.shape[1] * 0.6), :]
legend_length = np.linalg.norm(legend_rgb, axis=1, keepdims=True)
legend_vector = legend_rgb / np.maximum(legend_length, 1)
legend_brightness = np.maximum(legend_rgb.max(axis=1), 1)
palette = np.loadtxt(DATA / "vik.txt", dtype=np.float32)


def recolor(source_name: str, destination_name: str) -> None:
    source = np.asarray(Image.open(DATA / source_name).convert("RGB"), dtype=np.uint8)
    height, width, _ = source.shape
    flat = source.reshape(-1, 3).astype(np.float32)
    output = np.full_like(flat, 255, dtype=np.uint8)

    chunk_size = 30_000
    for start in range(0, len(flat), chunk_size):
        stop = min(len(flat), start + chunk_size)
        pixels = flat[start:stop]
        maximum = pixels.max(axis=1)
        minimum = pixels.min(axis=1)
        valid = ~((maximum > 244) & ((maximum - minimum) < 12))
        if not valid.any():
            continue

        valid_pixels = pixels[valid]
        pixel_length = np.linalg.norm(valid_pixels, axis=1, keepdims=True)
        pixel_vector = valid_pixels / np.maximum(pixel_length, 1)
        color_distance = ((pixel_vector[:, None, :] - legend_vector[None, :, :]) ** 2).sum(axis=2)
        pixel_brightness = np.maximum(valid_pixels.max(axis=1), 1)
        brightness_distance = np.abs(
            np.log(pixel_brightness[:, None] / legend_brightness[None, :])
        )
        nearest = np.argmin(color_distance + brightness_distance * 0.025, axis=1)
        matched_y = legend_y[nearest].astype(np.float32)
        anomaly = anomaly_at_y(matched_y)
        recolored = palette[vik_index(anomaly)] * 255

        relief = np.clip(
            (pixel_brightness / legend_brightness[nearest]) ** 0.18,
            0.82,
            1.18,
        )
        recolored = np.clip(recolored * relief[:, None], 0, 255).astype(np.uint8)
        chunk = output[start:stop]
        chunk[valid] = recolored

    Image.fromarray(output.reshape(height, width, 3), mode="RGB").save(
        DATA / destination_name,
        quality=92,
        optimize=True,
        progressive=True,
    )


def make_legend() -> None:
    result = np.asarray(legend_image).copy()
    for y in range(4, 460):
        value = anomaly_at_y(np.array([y], dtype=np.float32))[0]
        color = np.rint(palette[vik_index(np.array([value]))[0]] * 255).astype(np.uint8)
        result[y, 46:69, :] = color
    Image.fromarray(result, mode="RGB").save(DATA / "vik-legend.png", optimize=True)


recolor("total-field.jpg", "total-field-vik.jpg")
recolor("tilt-enhanced.jpg", "tilt-enhanced-vik.jpg")
make_legend()
