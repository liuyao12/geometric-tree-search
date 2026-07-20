#!/usr/bin/env python3
"""Render a learned Hat lattice marking as a PNG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from hat_marking_search import HAT_VERTS
from turtle_gcts_rl import Point, project_raw, scale


def color_for(value: int) -> str:
    if value < 0:
        palette = {
            1: "#2f80ed",
            2: "#174a9c",
            3: "#0b2f6b",
            4: "#081f49",
            5: "#0f3d73",
            6: "#155e9f",
            7: "#1d75bd",
        }
        return palette.get(abs(value), "#102a43")
    palette = {
        1: "#d55e00",
        2: "#9f2f00",
        3: "#7a1600",
        4: "#a04700",
        5: "#c96b00",
        6: "#e08214",
        7: "#f59f00",
    }
    return palette.get(abs(value), "#8c2d04")


def text_color_for(value: int) -> str:
    return "#ffffff" if abs(value) >= 2 else "#111111"


def channel_label(component: int) -> str:
    return ("X", "Y", "Z")[component] if 0 <= component < 3 else f"C{component}"


def value_name(value: int) -> str:
    names = {
        -2: "Navy",
        -1: "Blue",
        1: "Orange",
        2: "Rust",
    }
    if value in names:
        return names[value]
    return f"Blue {abs(value)}" if value < 0 else f"Orange {abs(value)}"


def load_fore_sites(path: Path) -> list[tuple[Point, int, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    segments = data["marking"]["segments"]
    sites = segments.get("site_fore", [])
    if not sites:
        raise ValueError(f"{path} does not contain site_fore marking data")
    out = []
    for item in sites:
        if len(item) == 2:
            point, value = item
            component = 0
        else:
            point, component, value = item
        out.append((tuple(point), int(component), int(value)))
    return out


def load_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def render(input_path: Path, output_path: Path, title: str) -> None:
    sites = load_fore_sites(input_path)
    polygon = [scale(point, 2) for point in HAT_VERTS]
    world_points = polygon + [point for point, _, _ in sites]
    projected = [project_raw(point) for point in world_points]
    min_x = min(point[0] for point in projected)
    max_x = max(point[0] for point in projected)
    min_y = min(point[1] for point in projected)
    max_y = max(point[1] for point in projected)

    scale_factor = 54
    margin = 90
    header = 86
    footer = 82
    width = int((max_x - min_x) * scale_factor + 2 * margin)
    height = int((max_y - min_y) * scale_factor + margin + header + footer)
    supersample = 2
    image = Image.new("RGB", (width * supersample, height * supersample), "#fbfaf7")
    draw = ImageDraw.Draw(image)

    def screen(point: Point) -> tuple[float, float]:
        x, y = project_raw(point)
        sx = (x - min_x) * scale_factor + margin
        sy = header + (max_y - y) * scale_factor + margin * 0.25
        return sx * supersample, sy * supersample

    def component_offset(component: int) -> tuple[float, float]:
        offsets = {
            0: (0.0, -15.0),
            1: (-13.0, 8.0),
            2: (13.0, 8.0),
        }
        dx, dy = offsets.get(component, (0.0, 0.0))
        return dx * supersample, dy * supersample

    title_font = load_font(24 * supersample)
    label_font = load_font(14 * supersample)
    small_font = load_font(12 * supersample)

    draw.text((margin * supersample, 22 * supersample), title, fill="#1f2933", font=title_font)
    subtitle = "Fore side shown. Rear side uses the same A2 sites with all signs negated."
    draw.text((margin * supersample, 55 * supersample), subtitle, fill="#52606d", font=small_font)

    poly = [screen(point) for point in polygon]
    draw.polygon(poly, fill="#f2eadf", outline="#4a3b2a")
    draw.line(poly + [poly[0]], fill="#4a3b2a", width=2 * supersample)

    radius = 14 * supersample
    components = {component for _, component, _ in sites}
    multi_component = len(components) > 1
    for point, component, value in sorted(sites, key=lambda item: (item[0], item[1], item[2])):
        x, y = screen(point)
        if multi_component:
            dx, dy = component_offset(component)
            x += dx
            y += dy
        fill = color_for(value)
        local_radius = radius if not multi_component else 11 * supersample
        draw.ellipse((x - local_radius, y - local_radius, x + local_radius, y + local_radius), fill=fill, outline="#1f2933", width=2 * supersample)
        label = channel_label(component) if multi_component else value_name(value)[0]
        bbox = draw.textbbox((0, 0), label, font=label_font)
        draw.text(
            (x - (bbox[2] - bbox[0]) / 2, y - (bbox[3] - bbox[1]) / 2 - 1 * supersample),
            label,
            fill=text_color_for(value),
            font=label_font,
        )

    legend_values = sorted({value for _, _, value in sites})
    legend_y = (height - 52) * supersample
    legend_x = margin * supersample
    draw.text((legend_x, legend_y - 20 * supersample), "Dot color = signed value; letter = channel", fill="#1f2933", font=small_font)
    cursor = legend_x
    for value in legend_values:
        fill = color_for(value)
        draw.ellipse(
            (cursor, legend_y + 2 * supersample, cursor + 18 * supersample, legend_y + 20 * supersample),
            fill=fill,
            outline="#1f2933",
            width=supersample,
        )
        label = value_name(value)
        draw.text((cursor + 24 * supersample, legend_y + 2 * supersample), label, fill="#1f2933", font=small_font)
        cursor += 108 * supersample

    image = image.resize((width, height), Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Hat lattice marking")
    return parser.parse_args()


def main() -> None:
    args = read_args()
    render(Path(args.input), Path(args.output), args.title)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
