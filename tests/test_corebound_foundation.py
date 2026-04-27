import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "corebound"


class CoreboundFoundationTests(unittest.TestCase):
    def test_static_entrypoint_wires_corebound_game_files(self) -> None:
        html = (GAME_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn("<title>Corebound</title>", html)
        self.assertIn('id="corebound-canvas"', html)
        self.assertIn("corebound-data.js", html)
        self.assertIn("corebound.js", html)
        self.assertIn("corebound.css", html)
        self.assertIn("Depth", html)
        self.assertIn("Cargo", html)
        self.assertIn("Hull", html)
        self.assertIn("Energy", html)
        self.assertIn("Heat", html)
        self.assertIn("Pressure", html)
        for control_id in (
            "sell-cargo",
            "refine-cargo",
            "repair-rig",
            "launch-run",
            "upgrade-list",
            "research-list",
            "heat-readout",
            "pressure-readout",
            "relic-readout",
        ):
            self.assertIn(control_id, html)

    def test_content_data_is_extendable_for_terrain_ores_economy_and_upgrades(self) -> None:
        data = (GAME_DIR / "corebound-data.js").read_text(encoding="utf-8")

        for key in (
            "world",
            "rig",
            "economy",
            "terrainTypes",
            "oreTypes",
            "hazardTypes",
            "depthBands",
            "upgrades",
            "researchProjects",
        ):
            self.assertIn(key, data)
        self.assertGreaterEqual(data.count("hardness"), 8)
        self.assertGreaterEqual(data.count("value"), 9)
        self.assertGreaterEqual(data.count("refine:"), 9)
        self.assertGreaterEqual(data.count("hazards:"), 5)
        for resource in ("credits", "alloy", "research", "relic"):
            self.assertIn(resource, data)
        for facility in ("refinery", "rigBay", "assayDesk"):
            self.assertIn(facility, data)
        for category in ("drill", "hull", "energy", "cargo", "scanner", "refinery", "survival", "mobility"):
            self.assertIn(f'category: "{category}"', data)
        self.assertIn("cargoCapacity", data)
        self.assertIn("maxEnergy", data)
        self.assertIn("maxHeat", data)
        self.assertIn("pressureMitigation", data)
        for project in ("thermalCartography", "faultPatterning", "ventChemistry", "resonantLift"):
            self.assertIn(project, data)

    def test_game_loop_contains_descent_surface_economy_and_upgrade_paths(self) -> None:
        script = (GAME_DIR / "corebound.js").read_text(encoding="utf-8")

        for behavior in (
            "generateWorld",
            "hazardForCell",
            "tryMove",
            "drillBlock",
            "applyHazardPressure",
            "pressureTier",
            "collectOre",
            "surfaceService",
            "sellCargo",
            "refineCargo",
            "repairRig",
            "purchaseUpgrade",
            "purchaseResearch",
            "launchRun",
            "rigStats",
            "renderResearchList",
            "updateHud",
        ):
            self.assertIn(behavior, script)
        self.assertIn("COREBOUND_DATA", script)
        self.assertIn("installedResearch", script)
        self.assertIn("keydown", script)


if __name__ == "__main__":
    unittest.main()
