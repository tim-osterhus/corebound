import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "corebound"
MANIFEST_PATH = GAME_DIR / "assets" / "asset-manifest.json"


UPGRADE_IDS = (
    "drillTorque",
    "hullLattice",
    "reserveCells",
    "cargoFrame",
    "assayLens",
    "refineryBaffles",
    "coolantVeins",
    "pressureSkids",
    "hazardSheath",
    "relicClamp",
)

RESEARCH_IDS = (
    "thermalCartography",
    "faultPatterning",
    "ventChemistry",
    "resonantLift",
)

ORE_KEYS = (
    "copperSeed",
    "saltglass",
    "cobaltThread",
    "nickelBloom",
    "emberFossil",
    "vaporCrystal",
    "prismMarrow",
    "archiveShard",
    "coreMote",
    "echoPearl",
    "relayCore",
)

HAZARD_KEYS = (
    "gasVent",
    "heatFissure",
    "pressureFault",
    "magneticBloom",
    "gravityShear",
)


def source_text(filename: str) -> str:
    return (GAME_DIR / filename).read_text(encoding="utf-8")


def manifest_short_paths() -> dict[str, str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        asset["id"]: asset["path"].removeprefix("games/corebound/")
        for asset in manifest["assets"]
    }


class CoreboundAssetIntegrationTests(unittest.TestCase):
    def test_data_asset_catalog_matches_shipping_manifest_paths(self) -> None:
        data = source_text("corebound-data.js")
        paths = manifest_short_paths()

        self.assertIn('sourceManifest: "assets/asset-manifest.json"', data)
        for asset_id, short_path in paths.items():
            self.assertIn(f'"{asset_id}"', data)
            self.assertIn(f'path: "{short_path}"', data)
            self.assertNotIn("://", short_path)
            self.assertFalse(Path(short_path).is_absolute())
            self.assertNotIn("..", Path(short_path).parts)

        for terrain in (
            "loam",
            "gritstone",
            "ironClay",
            "basaltLock",
            "pressureGlass",
            "thermalBasalt",
            "machineRib",
            "coreRind",
            "choirSlate",
            "anchorRib",
        ):
            self.assertRegex(data, rf"{terrain}: \"terrain\.(loam_gritstone|basalt_core|pressure_glass)_tile\"")

    def test_ui_asset_references_are_project_local_manifest_assets(self) -> None:
        paths = set(manifest_short_paths().values())
        files = {
            "corebound-data.js": source_text("corebound-data.js"),
            "corebound.css": source_text("corebound.css"),
            "index.html": source_text("index.html"),
        }

        for filename, text in files.items():
            for reference in re.findall(r'assets/[^"\'\)\s]+\.png', text):
                self.assertIn(reference, paths, f"{filename} references {reference}")
                self.assertNotIn("://", reference)
                self.assertFalse(Path(reference).is_absolute())

        self.assertIn('src="assets/surface/surface-facilities-panel.png"', files["index.html"])
        self.assertIn('background-image: url("assets/hud/hud-icon-atlas.png")', files["corebound.css"])

    def test_upgrade_and_research_rows_have_manifest_icon_slots_and_rig_modules(self) -> None:
        data = source_text("corebound-data.js")
        script = source_text("corebound.js")

        for entry_id in UPGRADE_IDS + RESEARCH_IDS:
            entry = re.search(rf'id: "{entry_id}",(?P<body>.*?)(?:effects|cost):', data, re.S)
            self.assertIsNotNone(entry, entry_id)
            self.assertIn("iconSlot:", entry.group("body"), entry_id)
            self.assertIn("rigModule:", entry.group("body"), entry_id)

        self.assertIn('makeAtlasIcon("upgrades.research_atlas", upgrade.iconSlot', script)
        self.assertIn('makeAtlasIcon("upgrades.research_atlas", project.iconSlot', script)
        self.assertIn("item.dataset.rigModule", script)

    def test_readable_atlas_maps_every_ore_and_hazard_key_used_by_renderer(self) -> None:
        data = source_text("corebound-data.js")
        script = source_text("corebound.js")

        for ore_key in ORE_KEYS:
            self.assertRegex(data, rf"{ore_key}: \d", ore_key)
        for hazard_key in HAZARD_KEYS:
            self.assertRegex(data, rf"{hazard_key}: \d", hazard_key)

        self.assertIn('drawAtlasSlot("readables.ore_hazard_atlas"', script)
        self.assertIn("drawOreMark(cell", script)
        self.assertIn("drawHazardMark(cell", script)

    def test_renderer_keeps_asset_backed_paths_and_fallbacks_explicit(self) -> None:
        script = source_text("corebound.js")

        for token in (
            "loadAssetImages",
            "loadedAsset",
            "drawSurfaceCell",
            "drawTextureTile",
            "drawReadableIcon",
            "drawPrimitiveRig",
            "drawRigFeedback",
            "installedRigModules",
            '"rig.mantis_motion_strip"',
            '"surface.facilities_panel"',
            '"surface.launch_shaft_context"',
            '"readables.ore_hazard_atlas"',
            "terrainTextureId(cell.terrain)",
            "ctx.drawImage(image",
            "ctx.imageSmoothingEnabled = true",
        ):
            self.assertIn(token, script)


if __name__ == "__main__":
    unittest.main()
