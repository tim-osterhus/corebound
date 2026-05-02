import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "void-prospector"
ASSET_DIR = GAME_DIR / "assets"
SHIPPING_MANIFEST_PATH = ASSET_DIR / "asset-manifest.json"
REQUEST_MANIFEST_PATH = ROOT / "_visual-check" / "void-prospector-assets" / "asset-request-manifest.json"
EVIDENCE_DIR = ROOT / "_visual-check" / "void-prospector-assets"
REQUEST_DIR = EVIDENCE_DIR / "asset-request"
DRY_RUN_REQUEST_DIR = EVIDENCE_DIR / "asset-request-dry-run"


EXPECTED_ASSETS = {
    "ship-decal": {
        "path": "games/void-prospector/assets/ship-decal.png",
        "role": "texture",
        "size": (256, 256),
        "alpha": True,
    },
    "asteroid-ore-glow": {
        "path": "games/void-prospector/assets/asteroid-ore-glow.png",
        "role": "texture",
        "size": (512, 512),
        "alpha": False,
    },
    "station-dock-panel": {
        "path": "games/void-prospector/assets/station-dock-panel.png",
        "role": "texture",
        "size": (512, 256),
        "alpha": False,
    },
    "pirate-marker": {
        "path": "games/void-prospector/assets/pirate-marker.png",
        "role": "sprite",
        "size": (256, 256),
        "alpha": True,
    },
    "arcade-title-card": {
        "path": "games/void-prospector/assets/arcade-title-card.png",
        "role": "background",
        "size": (800, 450),
        "alpha": False,
    },
}

EXPECTED_PROCEDURAL_ASSETS = {
    "ship-thruster-and-brake-glow": "games/void-prospector/void-prospector.js#createShipMesh",
    "asteroid-hit-glow-and-ore-sparks": "games/void-prospector/void-prospector.js#createOreSparks",
    "station-beacon-and-docking-corridor": "games/void-prospector/void-prospector.js#createStationMesh",
    "hud-radar-and-station-icons": "games/void-prospector/void-prospector.css",
    "pirate-warning-marker": "games/void-prospector/void-prospector.js#pirateWarningFeedback",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def png_header(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as file:
        signature = file.read(8)
        length, chunk_type = struct.unpack(">I4s", file.read(8))
        header = file.read(length)

    if signature != b"\x89PNG\r\n\x1a\n" or chunk_type != b"IHDR":
        raise AssertionError(f"{path} is not a valid PNG")
    width, height, _bit_depth, color_type = struct.unpack(">IIBB", header[:10])
    return width, height, color_type


def manifest_asset_path(asset: dict) -> Path:
    raw_path = Path(asset["path"])
    if raw_path.is_absolute():
        return raw_path
    return ROOT / raw_path


class VoidProspectorAssetPackTests(unittest.TestCase):
    def test_shipping_manifest_declares_complete_project_local_asset_pack(self) -> None:
        manifest = load_json(SHIPPING_MANIFEST_PATH)
        assets = manifest.get("assets")

        self.assertEqual(1, manifest.get("schema_version"))
        self.assertEqual("complete", manifest.get("status"))
        self.assertEqual("generate", manifest.get("mode"))
        self.assertEqual("_visual-check/void-prospector-assets/asset-request-manifest.json", manifest.get("request_manifest"))
        self.assertEqual(set(EXPECTED_ASSETS), {asset.get("id") for asset in assets})

        seen_paths = set()
        for asset in assets:
            expected = EXPECTED_ASSETS[asset["id"]]
            self.assertEqual(expected["path"], asset.get("path"))
            self.assertEqual(expected["role"], asset.get("role"))
            self.assertEqual(expected["size"][0], asset.get("width"))
            self.assertEqual(expected["size"][1], asset.get("height"))
            self.assertTrue(asset.get("description"))
            self.assertTrue(asset.get("intended_use"))
            self.assertTrue(asset.get("notes"))

            path = asset["path"]
            self.assertTrue(path.startswith("games/void-prospector/assets/"))
            self.assertFalse(Path(path).is_absolute())
            self.assertNotIn("://", path)
            self.assertNotIn("..", Path(path).parts)
            self.assertNotIn(path, seen_paths)
            seen_paths.add(path)
            self.assertTrue((ROOT / path).is_file(), path)

        shipped_pngs = {path.relative_to(ROOT).as_posix() for path in ASSET_DIR.rglob("*.png")}
        self.assertEqual(set(seen_paths), shipped_pngs)

    def test_shipping_manifest_declares_truthful_procedural_feedback_assets(self) -> None:
        manifest = load_json(SHIPPING_MANIFEST_PATH)
        procedural_assets = {asset.get("id"): asset for asset in manifest.get("procedural_assets", [])}

        self.assertEqual(set(EXPECTED_PROCEDURAL_ASSETS), set(procedural_assets))
        for asset_id, expected_path in EXPECTED_PROCEDURAL_ASSETS.items():
            asset = procedural_assets[asset_id]
            self.assertEqual(expected_path, asset.get("path"))
            self.assertIn(asset.get("role"), {"procedural-mesh", "procedural-css", "procedural-state"})
            self.assertTrue(asset.get("description"))
            self.assertTrue(asset.get("intended_use"))
            self.assertTrue((ROOT / expected_path.split("#", 1)[0]).is_file())

    def test_request_manifest_and_visual_pipeline_evidence_are_preserved(self) -> None:
        manifest = load_json(REQUEST_MANIFEST_PATH)
        meta = load_json(REQUEST_DIR / "request-meta.json")
        prompt = (REQUEST_DIR / "request-prompt.md").read_text(encoding="utf-8")
        dry_run_meta = load_json(DRY_RUN_REQUEST_DIR / "request-meta.json")
        dry_run_prompt = (DRY_RUN_REQUEST_DIR / "request-prompt.md").read_text(encoding="utf-8")

        self.assertEqual("complete", manifest.get("status"))
        self.assertEqual("generate", manifest.get("mode"))
        self.assertEqual(set(EXPECTED_ASSETS), {asset.get("id") for asset in manifest["assets"]})
        self.assertFalse(meta["dry_run"])
        self.assertTrue(meta["manifest"].endswith("_visual-check/void-prospector-assets/asset-request-manifest.json"))
        self.assertTrue(meta["out_dir"].endswith("games/void-prospector/assets"))
        self.assertIn("$imagegen", prompt)
        self.assertIn("Do not use OPENAI_API_KEY", prompt)
        self.assertTrue(dry_run_meta["dry_run"])
        self.assertTrue(dry_run_meta["manifest"].endswith("_visual-check/void-prospector-assets/asset-request-manifest.json"))
        self.assertTrue(dry_run_meta["out_dir"].endswith("games/void-prospector/assets"))
        self.assertIn("$imagegen", dry_run_prompt)
        self.assertIn("Do not use OPENAI_API_KEY", dry_run_prompt)

        for filename in (
            "request-prompt.md",
            "request-meta.json",
            "codex-summary.md",
            "codex-stdout.log",
            "codex-stderr.log",
            "source-contact-sheet.png",
            "final-contact-sheet.png",
        ):
            self.assertTrue((REQUEST_DIR / filename).is_file(), filename)
        for filename in ("request-prompt.md", "request-meta.json"):
            self.assertTrue((DRY_RUN_REQUEST_DIR / filename).is_file(), filename)

        for asset in manifest["assets"]:
            self.assertTrue(manifest_asset_path(asset).is_file(), asset["path"])

    def test_generated_pngs_match_manifest_dimensions_and_alpha_contract(self) -> None:
        for asset_id, expected in EXPECTED_ASSETS.items():
            width, height, color_type = png_header(ROOT / expected["path"])

            self.assertEqual(expected["size"], (width, height), asset_id)
            if expected["alpha"]:
                self.assertIn(color_type, (4, 6), asset_id)

    def test_asset_roles_cover_void_prospector_required_surfaces(self) -> None:
        manifest = load_json(SHIPPING_MANIFEST_PATH)
        ids = {asset["id"] for asset in manifest["assets"]}

        self.assertIn("ship-decal", ids)
        self.assertIn("asteroid-ore-glow", ids)
        self.assertIn("station-dock-panel", ids)
        self.assertIn("pirate-marker", ids)
        self.assertIn("arcade-title-card", ids)

        procedural_ids = {asset["id"] for asset in manifest.get("procedural_assets", [])}
        self.assertIn("ship-thruster-and-brake-glow", procedural_ids)
        self.assertIn("asteroid-hit-glow-and-ore-sparks", procedural_ids)
        self.assertIn("station-beacon-and-docking-corridor", procedural_ids)
        self.assertIn("hud-radar-and-station-icons", procedural_ids)
        self.assertIn("pirate-warning-marker", procedural_ids)


if __name__ == "__main__":
    unittest.main()
