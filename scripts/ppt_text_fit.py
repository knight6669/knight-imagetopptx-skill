#!/usr/bin/env python3
"""Estimate PowerPoint text fit with real Windows font metrics.

This is a preflight helper for image-to-PPTX rebuilds. It estimates the largest
PowerPoint point size that fits a target pixel box after PPT export, preserving
explicit line breaks and wrapping CJK text conservatively.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FONT_MAP = {
    "microsoft yahei": ("msyh.ttc", "msyhbd.ttc"),
    "微软雅黑": ("msyh.ttc", "msyhbd.ttc"),
    "simhei": ("simhei.ttf", "simhei.ttf"),
    "黑体": ("simhei.ttf", "simhei.ttf"),
    "arial": ("arial.ttf", "arialbd.ttf"),
}


def parse_pair(value: str, sep: str) -> tuple[float, float]:
    left, right = value.lower().split(sep, 1)
    return float(left), float(right)


def find_font(font_name: str, bold: bool) -> Path:
    fonts_dir = Path("C:/Windows/Fonts")
    key = font_name.strip().lower()
    regular, bold_file = FONT_MAP.get(key, ("msyh.ttc", "msyhbd.ttc"))
    path = fonts_dir / (bold_file if bold else regular)
    if path.exists():
        return path
    fallback = fonts_dir / regular
    if fallback.exists():
        return fallback
    return fonts_dir / "msyh.ttc"


def char_width(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, text: str) -> float:
    if text == "":
        return 0.0
    box = draw.textbbox((0, 0), text, font=font)
    return max(0.0, box[2] - box[0])


def tokenize(text: str) -> list[str]:
    # Keep Latin/number runs together, but allow CJK to wrap character by character.
    return re.findall(r"[A-Za-z0-9_./:+#-]+|\s+|.", text, flags=re.DOTALL)


def wrap_paragraph(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, text: str, max_width: float) -> list[str]:
    tokens = tokenize(text)
    lines: list[str] = []
    current = ""
    for token in tokens:
        if token == "\n":
            lines.append(current.rstrip())
            current = ""
            continue
        candidate = current + token
        if current and char_width(draw, font, candidate) > max_width:
            lines.append(current.rstrip())
            current = token.lstrip()
            if char_width(draw, font, current) > max_width and len(current) > 1:
                # Break an over-wide Latin token or long unspaced run.
                broken = ""
                for ch in current:
                    if broken and char_width(draw, font, broken + ch) > max_width:
                        lines.append(broken)
                        broken = ch
                    else:
                        broken += ch
                current = broken
        else:
            current = candidate
    lines.append(current.rstrip())
    return [line for line in lines if line != ""]


def measure(
    text: str,
    pt: float,
    font_path: Path,
    px_per_pt: float,
    width_px: float,
    line_spacing: float,
    width_safety: float,
    render_fudge: float,
) -> dict:
    font_px = max(1, int(round(pt * px_per_pt * render_fudge)))
    font = ImageFont.truetype(str(font_path), font_px)
    canvas = Image.new("RGB", (max(4, int(width_px * 2)), 4000), "white")
    draw = ImageDraw.Draw(canvas)
    safe_width = width_px * width_safety
    lines: list[str] = []
    for para in text.split("\n"):
        lines.extend(wrap_paragraph(draw, font, para, safe_width))
    if not lines:
        lines = [""]
    boxes = [draw.textbbox((0, 0), line if line else "口", font=font) for line in lines]
    widths = [max(0.0, box[2] - box[0]) for box in boxes]
    glyph_heights = [max(0.0, box[3] - box[1]) for box in boxes]
    # PowerPoint text boxes are closer to visible glyph bounds than full font
    # ascent+descent. Add a modest line gap to avoid over-shrinking CJK labels.
    line_height = max(max(glyph_heights) if glyph_heights else 0.0, font_px * 0.82) * line_spacing
    height = line_height * len(lines)
    return {
        "pt": pt,
        "font_px": font_px,
        "lines": lines,
        "line_count": len(lines),
        "width_px": max(widths) if widths else 0,
        "height_px": height,
        "line_height_px": line_height,
    }


def best_fit(args) -> dict:
    box_w, box_h = parse_pair(args.box, "x")
    slide_w_px, _ = parse_pair(args.slide_px, "x")
    slide_w_in, _ = parse_pair(args.slide_in, "x")
    px_per_pt = (slide_w_px / slide_w_in) / 72.0
    font_path = find_font(args.font, args.bold)

    lo, hi = args.min_pt, args.max_pt
    best = None
    for _ in range(18):
        mid = (lo + hi) / 2.0
        result = measure(
            args.text,
            mid,
            font_path,
            px_per_pt,
            box_w,
            args.line_spacing,
            args.width_safety,
            args.render_fudge,
        )
        fits = (
            result["width_px"] <= box_w * args.width_safety
            and result["height_px"] <= box_h * args.height_safety
            and (args.max_lines <= 0 or result["line_count"] <= args.max_lines)
        )
        if fits:
            best = result
            lo = mid
        else:
            hi = mid

    if best is None:
        best = measure(
            args.text,
            args.min_pt,
            font_path,
            px_per_pt,
            box_w,
            args.line_spacing,
            args.width_safety,
            args.render_fudge,
        )
    best["recommended_pt"] = round(best["pt"], 2)
    best["font_path"] = str(font_path)
    best["px_per_pt"] = px_per_pt
    best["box_px"] = [box_w, box_h]
    best["fits"] = (
        best["width_px"] <= box_w * args.width_safety
        and best["height_px"] <= box_h * args.height_safety
        and (args.max_lines <= 0 or best["line_count"] <= args.max_lines)
    )
    best["settings"] = {
        "font": args.font,
        "bold": args.bold,
        "max_lines": args.max_lines,
        "line_spacing": args.line_spacing,
        "width_safety": args.width_safety,
        "height_safety": args.height_safety,
        "render_fudge": args.render_fudge,
    }
    return best


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--box", required=True, help="Target box in exported pixels, e.g. 780x42")
    parser.add_argument("--font", default="Microsoft YaHei")
    parser.add_argument("--bold", action="store_true")
    parser.add_argument("--min-pt", type=float, default=8)
    parser.add_argument("--max-pt", type=float, default=36)
    parser.add_argument("--max-lines", type=int, default=0, help="0 means unlimited")
    parser.add_argument("--line-spacing", type=float, default=1.06)
    parser.add_argument("--width-safety", type=float, default=0.92)
    parser.add_argument("--height-safety", type=float, default=0.95)
    parser.add_argument("--render-fudge", type=float, default=1.01)
    parser.add_argument("--slide-px", default="1672x941")
    parser.add_argument("--slide-in", default="13.333333x7.505")
    args = parser.parse_args()
    print(json.dumps(best_fit(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
