import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "games" / "corebound" / "assets"
MANIFEST_PATH = ASSET_DIR / "asset-manifest.json"
EVIDENCE_DIR = ROOT / "_visual-check" / "corebound-assets" / "asset-request"


EXPECTED_ASSETS = {
    "rig.mantis_motion_strip": {
        "path": "games/corebound/assets/rig/mantis-rig-motion-strip.png",
        "role": "sprite-strip",
        "size": (320, 80),
        "alpha": True,
    },
    "surface.facilities_panel": {
        "path": "games/corebound/assets/surface/surface-facilities-panel.png",
        "role": "background",
        "size": (640, 160),
        "alpha": False,
    },
    "surface.launch_shaft_context": {
        "path": "games/corebound/assets/surface/launch-shaft-context.png",
        "role": "background",
        "size": (320, 320),
        "alpha": False,
    },
    "terrain.loam_gritstone_tile": {
        "path": "games/corebound/assets/terrain/loam-gritstone-tile.png",
        "role": "texture",
        "size": (128, 128),
        "alpha": False,
    },
    "terrain.basalt_core_tile": {
        "path": "games/corebound/assets/terrain/basalt-core-tile.png",
        "role": "texture",
        "size": (128, 128),
        "alpha": False,
    },
    "terrain.pressure_glass_tile": {
        "path": "games/corebound/assets/terrain/pressure-glass-tile.png",
        "role": "texture",
        "size": (128, 128),
        "alpha": False,
    },
    "readables.ore_hazard_atlas": {
        "path": "games/corebound/assets/readables/ore-hazard-atlas.png",
        "role": "icon",
        "size": (384, 128),
        "alpha": True,
    },
    "hud.icon_atlas": {
        "path": "games/corebound/assets/hud/hud-icon-atlas.png",
        "role": "icon",
        "size": (320, 64),
        "alpha": True,
    },
    "upgrades.research_atlas": {
        "path": "games/corebound/assets/upgrades/upgrade-research-atlas.png",
        "role": "icon",
        "size": (512, 128),
        "alpha": True,
    },
}


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def png_header(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as file:
        signature = file.read(8)
        length, chunk_type = struct.unpack(">I4s", file.read(8))
        self_describing_header = file.read(length)

    if signature != b"\x89PNG\r\n\x1a\n" or chunk_type != b"IHDR":
        raise AssertionError(f"{path} is not a valid PNG")
    width, height, _bit_depth, color_type = struct.unpack(">IIBB", self_describing_header[:10])
    return width, height, color_type


class CoreboundAssetPackTests(unittest.TestCase):
    def test_shipping_manifest_declares_complete_local_asset_pack(self) -> None:
        manifest = load_manifest()
        assets = manifest.get("assets")

        self.assertEqual(1, manifest.get("schema_version"))
        self.assertEqual("complete", manifest.get("status"))
        self.assertEqual("generate", manifest.get("mode"))
        self.assertTrue(str(manifest.get("workdir", "")).endswith("/auto-games"))
        self.assertIsInstance(assets, list)
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
            self.assertTrue(path.startswith("games/corebound/assets/"))
            self.assertFalse(Path(path).is_absolute())
            self.assertNotIn("://", path)
            self.assertNotIn("..", Path(path).parts)
            self.assertNotIn(path, seen_paths)
            seen_paths.add(path)
            self.assertTrue((ROOT / path).is_file(), path)

        shipped_pngs = {
            path.relative_to(ROOT).as_posix()
            for path in ASSET_DIR.rglob("*.png")
        }
        self.assertEqual(set(seen_paths), shipped_pngs)

    def test_generated_pngs_match_manifest_dimensions_and_alpha_contract(self) -> None:
        for asset_id, expected in EXPECTED_ASSETS.items():
            width, height, color_type = png_header(ROOT / expected["path"])

            self.assertEqual(expected["size"], (width, height), asset_id)
            if expected["alpha"]:
                self.assertIn(color_type, (4, 6), asset_id)

    def test_asset_roles_cover_corebound_spec_surfaces(self) -> None:
        manifest = load_manifest()
        ids = {asset["id"] for asset in manifest["assets"]}

        for required_id in (
            "rig.mantis_motion_strip",
            "surface.facilities_panel",
            "surface.launch_shaft_context",
            "terrain.loam_gritstone_tile",
            "terrain.basalt_core_tile",
            "terrain.pressure_glass_tile",
            "readables.ore_hazard_atlas",
            "hud.icon_atlas",
            "upgrades.research_atlas",
        ):
            self.assertIn(required_id, ids)

    def test_visual_asset_pipeline_evidence_is_local_and_replayable(self) -> None:
        prompt = EVIDENCE_DIR / "request-prompt.md"
        meta = json.loads((EVIDENCE_DIR / "request-meta.json").read_text(encoding="utf-8"))

        for filename in (
            "request-prompt.md",
            "request-meta.json",
            "codex-summary.md",
            "codex-stdout.log",
            "codex-stderr.log",
        ):
            self.assertTrue((EVIDENCE_DIR / filename).is_file(), filename)

        prompt_text = prompt.read_text(encoding="utf-8")
        self.assertIn("$imagegen", prompt_text)
        self.assertIn("Do not use OPENAI_API_KEY", prompt_text)
        self.assertFalse(meta["dry_run"])
        self.assertTrue(meta["manifest"].endswith("games/corebound/assets/asset-manifest.json"))
        self.assertTrue(meta["out_dir"].endswith("games/corebound/assets"))


if __name__ == "__main__":
    unittest.main()
