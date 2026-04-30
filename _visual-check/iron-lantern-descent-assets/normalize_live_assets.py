#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "games" / "iron-lantern-descent" / "assets"
EVIDENCE_DIR = ROOT / "_visual-check" / "iron-lantern-descent-assets"
REQUEST_DIR = EVIDENCE_DIR / "asset-request"
REQUEST_MANIFEST = EVIDENCE_DIR / "asset-request-manifest.json"
SHIPPING_MANIFEST = ASSET_DIR / "asset-manifest.json"
CONTACT_SHEET = EVIDENCE_DIR / "asset-contact-sheet.png"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fit_opaque(source: Path, destination: Path, size: tuple[int, int]) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    src_ratio = image.width / image.height
    dst_ratio = size[0] / size[1]
    if src_ratio > dst_ratio:
        crop_width = int(image.height * dst_ratio)
        left = (image.width - crop_width) // 2
        image = image.crop((left, 0, left + crop_width, image.height))
    elif src_ratio < dst_ratio:
        crop_height = int(image.width / dst_ratio)
        top = (image.height - crop_height) // 2
        image = image.crop((0, top, image.width, top + crop_height))
    image = image.resize(size, Image.Resampling.LANCZOS)
    image.save(destination)


def fit_alpha(source: Path, destination: Path, size: tuple[int, int], padding: int = 16) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)
    max_width = size[0] - padding * 2
    max_height = size[1] - padding * 2
    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    canvas.save(destination)


def resize_alpha(source: Path, destination: Path, size: tuple[int, int]) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
    image = image.resize(size, Image.Resampling.LANCZOS)
    image.save(destination)


def normalize_assets() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    fit_alpha(REQUEST_DIR / "lantern-anchor-alpha.png", ASSET_DIR / "lantern-anchor.png", (256, 256), padding=12)
    fit_opaque(REQUEST_DIR / "mineral-vein-material-source.png", ASSET_DIR / "mineral-vein-material.png", (512, 512))
    fit_alpha(REQUEST_DIR / "drill-tool-alpha.png", ASSET_DIR / "drill-tool.png", (256, 256), padding=10)
    resize_alpha(REQUEST_DIR / "oxygen-light-icons-alpha.png", ASSET_DIR / "oxygen-light-icons.png", (384, 128))
    fit_opaque(REQUEST_DIR / "arcade-title-card-source.png", ASSET_DIR / "arcade-title-card.png", (800, 450))


def write_manifest() -> None:
    assets = [
        {
            "id": "lantern-anchor",
            "path": "games/iron-lantern-descent/assets/lantern-anchor.png",
            "role": "sprite",
            "description": "Transparent iron lantern anchor treatment with cage, warm core, clamp hardware, and teal alignment signal.",
            "width": 256,
            "height": 256,
            "intended_use": "In-world route anchor sprite and lantern mesh texture.",
            "notes": "Generated with Codex built-in image generation on a chroma-key source, converted to alpha, cropped, and resized to 256x256 PNG.",
        },
        {
            "id": "mineral-vein-material",
            "path": "games/iron-lantern-descent/assets/mineral-vein-material.png",
            "role": "texture",
            "description": "Opaque cave mineral material with dark rock, teal crystal interference seams, and amber ore flecks.",
            "width": 512,
            "height": 512,
            "intended_use": "Three.js cave floor and mineable sample node material texture.",
            "notes": "Generated with Codex built-in image generation and center-cropped/resized to exact square texture dimensions.",
        },
        {
            "id": "drill-tool",
            "path": "games/iron-lantern-descent/assets/drill-tool.png",
            "role": "sprite",
            "description": "Transparent compact handheld drill/sample tool with steel body, bit, work lamp, and teal status stripe.",
            "width": 256,
            "height": 256,
            "intended_use": "Close-third-person player drill sprite and mining tool visual cue.",
            "notes": "Generated with Codex built-in image generation on a chroma-key source, converted to alpha, cropped, and resized to 256x256 PNG.",
        },
        {
            "id": "oxygen-light-icons",
            "path": "games/iron-lantern-descent/assets/oxygen-light-icons.png",
            "role": "icon",
            "description": "Transparent three-cell atlas for oxygen tank, lantern light, and scanner route-pulse icons.",
            "width": 384,
            "height": 128,
            "intended_use": "HUD oxygen, light, and scanner icon atlas.",
            "notes": "Generated with Codex built-in image generation on a chroma-key source, converted to alpha, and resized to a 3x128 icon atlas.",
        },
        {
            "id": "arcade-title-card",
            "path": "games/iron-lantern-descent/assets/arcade-title-card.png",
            "role": "background",
            "description": "Opaque title-card art showing a cave descent from the iron lift with route lanterns, mineral veins, and drill cues.",
            "width": 800,
            "height": 450,
            "intended_use": "Game title-card band and arcade thumbnail art.",
            "notes": "Generated with Codex built-in image generation and center-cropped/resized to exact 16:9 dimensions.",
        },
    ]
    request_payload = {
        "schema_version": 1,
        "status": "complete",
        "mode": "generate",
        "workdir": str(ROOT),
        "assets": assets,
        "notes": (
            "Original Iron Lantern Descent asset pack generated through the visual-asset-pipeline Codex bridge. "
            "The live bridge produced source rasters but was interrupted before writing its manifest, so the "
            "source files are preserved under asset-request and normalized locally into exact shipping dimensions."
        ),
    }
    shipping_payload = {
        **request_payload,
        "request_manifest": "_visual-check/iron-lantern-descent-assets/asset-request-manifest.json",
        "notes": "Original Iron Lantern Descent raster asset pack generated through the visual-asset-pipeline Codex bridge; final project-consumed PNGs are local under games/iron-lantern-descent/assets.",
    }
    REQUEST_MANIFEST.write_text(json.dumps(request_payload, indent=2) + "\n", encoding="utf-8")
    SHIPPING_MANIFEST.write_text(json.dumps(shipping_payload, indent=2) + "\n", encoding="utf-8")


def save_contact_sheet() -> None:
    sheet = Image.new("RGBA", (900, 660), (8, 12, 11, 255))
    placements = [
        ("lantern-anchor.png", (30, 30), (190, 190)),
        ("drill-tool.png", (250, 30), (190, 190)),
        ("oxygen-light-icons.png", (470, 64), (360, 120)),
        ("mineral-vein-material.png", (40, 290), (210, 210)),
        ("arcade-title-card.png", (310, 285), (520, 292)),
    ]
    for filename, origin, size in placements:
        with Image.open(ASSET_DIR / filename) as opened:
            image = opened.convert("RGBA")
            image.thumbnail(size, Image.Resampling.LANCZOS)
        sheet.alpha_composite(image, origin)
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> None:
    normalize_assets()
    write_manifest()
    save_contact_sheet()
    print(json.dumps({"assets": [rel(path) for path in sorted(ASSET_DIR.glob("*.png"))], "manifest": rel(REQUEST_MANIFEST)}, indent=2))


if __name__ == "__main__":
    main()
