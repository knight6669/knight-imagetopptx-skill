from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def check_asset_dir(asset_dir: Path, min_padding: int) -> list[str]:
    errors: list[str] = []
    pngs = sorted(asset_dir.glob("*.png"))
    if not pngs:
        return [f"no PNG assets found in {asset_dir}"]

    for path in pngs:
        with Image.open(path) as im:
            rgba = im.convert("RGBA")
        alpha = rgba.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            errors.append(f"{path.name}: empty alpha channel")
            continue

        left, top, right, bottom = bbox
        pads = (left, top, rgba.width - right, rgba.height - bottom)
        if min(pads) < min_padding:
            errors.append(f"{path.name}: unsafe transparent padding {pads}; expected all >= {min_padding}px")

        pix = rgba.load()
        edge_hits = 0
        for x in range(rgba.width):
            if pix[x, 0][3] or pix[x, rgba.height - 1][3]:
                edge_hits += 1
        for y in range(rgba.height):
            if pix[0, y][3] or pix[rgba.width - 1, y][3]:
                edge_hits += 1
        if edge_hits:
            errors.append(f"{path.name}: non-transparent pixels touch image edge ({edge_hits} hits)")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Check generated transparent icon assets for image-to-editable-PPTX rebuilds.")
    parser.add_argument("--asset-dir", type=Path, required=True, help="Directory containing generated transparent PNG assets.")
    parser.add_argument("--pptx", type=Path, help="Accepted for compatibility; PPTX media is not inspected.")
    parser.add_argument("--min-padding", type=int, default=10, help="Minimum transparent edge padding in pixels.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    args = parser.parse_args()

    errors = check_asset_dir(args.asset_dir, args.min_padding)

    result = {"ok": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PASSED" if result["ok"] else "FAILED")
        for error in errors:
            print(f"- {error}")

    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
