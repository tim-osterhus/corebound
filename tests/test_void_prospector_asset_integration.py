import json
import re
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "void-prospector"
MANIFEST_PATH = GAME_DIR / "assets" / "asset-manifest.json"


def source_text(filename: str) -> str:
    return (GAME_DIR / filename).read_text(encoding="utf-8")


def manifest_short_paths() -> set[str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        asset["path"].removeprefix("games/void-prospector/")
        for asset in manifest["assets"]
    }


class VoidProspectorAssetIntegrationTests(unittest.TestCase):
    def test_static_asset_references_are_project_local_manifest_assets(self) -> None:
        paths = manifest_short_paths()
        files = {
            "index.html": source_text("index.html"),
            "void-prospector.css": source_text("void-prospector.css"),
            "void-prospector.js": source_text("void-prospector.js"),
        }

        for filename, text in files.items():
            for reference in re.findall(r'assets/[^"\'\)\s]+\.png', text):
                self.assertIn(reference, paths, f"{filename} references {reference}")
                self.assertNotIn("://", reference)
                self.assertFalse(Path(reference).is_absolute())

        self.assertIn('src="assets/arcade-title-card.png"', files["index.html"])
        self.assertIn('sourceManifest: "assets/asset-manifest.json"', files["void-prospector.js"])

    def test_scene_asset_loader_uses_generated_texture_paths(self) -> None:
        script = source_text("void-prospector.js")
        css = source_text("void-prospector.css")

        for token in (
            "ASSET_PATHS",
            "loadSceneAssets",
            "TextureLoader",
            'shipDecal: "assets/ship-decal.png"',
            'asteroidOreGlow: "assets/asteroid-ore-glow.png"',
            'stationDockPanel: "assets/station-dock-panel.png"',
            'pirateMarker: "assets/pirate-marker.png"',
            'arcadeTitleCard: "assets/arcade-title-card.png"',
            "sceneAssets",
            "emissiveMap: assets.asteroidOreGlow",
            "map: assets.stationDockPanel",
            "map: assets.pirateMarker",
            "createOreSparks",
            "thrusterGlows",
            "brakeGlows",
            "dockingCorridor",
            "stationBeacon",
            "oreHalo",
            "pirateWarningFeedback",
            "cockpitFeedbackSurface",
        ):
            self.assertIn(token, script)

        html = source_text("index.html")
        for token in (
            ".title-card-band",
            "object-fit: cover",
            'data-kind="cargo"',
            'data-kind="fuel"',
            'data-kind="repair"',
            'data-kind="contract"',
        ):
            source = {
                "css": css,
                "html": html,
            }
            self.assertTrue(any(token in text for text in source.values()), token)

        for token in (
            ".station-summary-grid span::before",
            '.station-summary-grid span[data-kind="cargo"]::before',
            '.station-upgrade-list button[data-kind="beam-upgrade"]::before',
            '.world-label[data-state="warning"]',
            '.prospector-shell[data-thrust="active"]',
            '.prospector-shell[data-mining="active"]',
            '.prospector-shell[data-docking="dockable"]',
            '.radar-blip[data-kind="asteroid"]',
        ):
            self.assertIn(token, css)

    def test_asset_manifest_declares_procedural_feedback_roles_truthfully(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        procedural = {asset["id"]: asset for asset in manifest["procedural_assets"]}

        expected = {
            "ship-thruster-and-brake-glow": "games/void-prospector/void-prospector.js#createShipMesh",
            "asteroid-hit-glow-and-ore-sparks": "games/void-prospector/void-prospector.js#createOreSparks",
            "station-beacon-and-docking-corridor": "games/void-prospector/void-prospector.js#createStationMesh",
            "hud-radar-and-station-icons": "games/void-prospector/void-prospector.css",
            "pirate-warning-marker": "games/void-prospector/void-prospector.js#pirateWarningFeedback",
        }
        self.assertEqual(set(expected), set(procedural))
        for asset_id, path in expected.items():
            self.assertEqual(path, procedural[asset_id]["path"])
            self.assertTrue(procedural[asset_id]["description"])
            self.assertTrue(procedural[asset_id]["intended_use"])
            self.assertTrue((ROOT / path.split("#", 1)[0]).is_file())

    def test_cockpit_feedback_surface_exposes_mining_docking_ship_and_pirate_hooks(self) -> None:
        result = json.loads(
            self.run_node_script(
                """
                const state0 = game.createInitialState({ seed: 33 });
                const node = state0.asteroids[0];

                let thrustState = game.stepSpaceflight(state0, { thrust: true }, 1);
                let brakeState = game.stepSpaceflight(thrustState, { brake: true }, 1);

                let miningState = game.createInitialState({ seed: 33 });
                miningState.ship.position = { x: node.position.x + 2, y: node.position.y, z: node.position.z + 1 };
                miningState.ship.velocity = { x: 0, y: 0, z: 0 };
                miningState = game.setTarget(miningState, "asteroid", node.id);
                miningState = game.stepSpaceflight(miningState, { mine: true }, 1);
                const miningSurface = game.surveyCockpitSurface(miningState).cockpit.feedback;
                const cooldownSurface = game.surveyCockpitSurface(game.stepSpaceflight(miningState, {}, 1)).cockpit.feedback;
                let depletedState = miningState;
                for (let index = 0; index < 4; index += 1) {
                  depletedState = game.stepSpaceflight(depletedState, { mine: true }, 1);
                }
                const depletedSurface = game.surveyCockpitSurface(depletedState).cockpit.feedback;

                let dockState = depletedState;
                dockState.ship.position = { ...dockState.station.position };
                dockState.ship.hull = 61;
                dockState.ship.fuel = 24;
                dockState.ship.velocity = { x: 0, y: 0, z: 0 };
                dockState = game.stepSpaceflight(dockState, { interact: true }, 1);
                const dockSurface = game.surveyCockpitSurface(dockState).cockpit.feedback;
                const warningSurface = game.surveyCockpitSurface(dockState).cockpit;
                let threatState = dockState;
                for (let index = 0; index < 7; index += 1) {
                  threatState = game.stepSpaceflight(threatState, {}, 1);
                }
                const threatSurface = game.surveyCockpitSurface(threatState).cockpit;

                console.log(JSON.stringify({
                  thrustGlow: game.surveyCockpitSurface(thrustState).cockpit.feedback.ship.thrustGlow,
                  brakeGlow: game.surveyCockpitSurface(brakeState).cockpit.feedback.ship.brakeGlow,
                  mining: miningSurface.mining,
                  cooldown: cooldownSurface.mining,
                  depleted: depletedSurface.mining,
                  docking: dockSurface.docking,
                  warningThreat: warningSurface.feedback.threat,
                  warningLabel: warningSurface.labels.threat,
                  warningRadar: warningSurface.radar.blips.map((blip) => blip.kind),
                  warningPrompts: warningSurface.prompts,
                  liveThreat: threatSurface.feedback.threat,
                  liveLabel: threatSurface.labels.threat,
                }));
                """
            )
        )

        self.assertEqual("active", result["thrustGlow"])
        self.assertEqual("active", result["brakeGlow"])
        self.assertTrue(result["mining"]["beamActive"])
        self.assertEqual("active", result["mining"]["hitGlow"])
        self.assertEqual("ore-yield", result["mining"]["sparkState"])
        self.assertGreater(result["mining"]["oreParticles"], 0)
        self.assertGreaterEqual(result["mining"]["cargoDelta"], 1)
        self.assertGreater(result["mining"]["heat"], 0)
        self.assertEqual("cooldown", result["cooldown"]["hitGlow"])
        self.assertTrue(result["cooldown"]["cooldown"])
        self.assertTrue(result["depleted"]["depleted"])
        self.assertEqual("docked", result["docking"]["state"])
        self.assertTrue(result["docking"]["successfulDock"])
        self.assertGreater(result["docking"]["cargoSaleCredits"], 0)
        self.assertIn("Fuel", result["docking"]["refuelSummary"])
        self.assertIn("repaired", result["docking"]["repairSummary"])
        self.assertEqual("refined-beam", result["docking"]["upgradePreview"]["id"])
        self.assertIn(result["warningThreat"]["stage"], ("warning", "imminent"))
        self.assertEqual("warning", result["warningLabel"]["state"])
        self.assertIn("threat", result["warningRadar"])
        self.assertTrue(any("decoy" in prompt.lower() for prompt in result["warningPrompts"]))
        self.assertIn(result["liveThreat"]["stage"], ("shadow", "contact", "close"))
        self.assertEqual("threat", result["liveLabel"]["state"])

    def test_derelict_salvage_visuals_are_procedural_and_keep_raster_manifest_local(self) -> None:
        script = source_text("void-prospector.js")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        for token in (
            "createSalvageMesh",
            "syncSalvageMeshes",
            "salvageMeshes",
            "new THREE.BoxGeometry",
            "new THREE.TorusGeometry",
            "new THREE.TetrahedronGeometry",
            "state.target.kind === \"salvage\"",
            "0xd0b36a",
        ):
            self.assertIn(token, script)

        self.assertEqual("complete", manifest["status"])
        self.assertEqual("assets/asset-manifest.json", json.loads(self.run_node("game.GAME_DATA.assets"))["sourceManifest"])
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*salvage[^"\'\)\s]*\.png')

    def test_beacon_convoy_and_storm_visuals_are_procedural_and_keep_raster_manifest_local(self) -> None:
        script = source_text("void-prospector.js")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_paths = {asset["path"].removeprefix("games/void-prospector/") for asset in manifest["assets"]}

        for token in (
            "createConvoyMesh",
            "syncConvoyMeshes",
            "convoyMeshes",
            "createStormMesh",
            "syncStormMeshes",
            "stormMeshes",
            "new THREE.CylinderGeometry",
            "new THREE.TorusGeometry",
            "new THREE.IcosahedronGeometry",
            "new THREE.BufferGeometry().setFromPoints",
            "new THREE.TetrahedronGeometry",
            "state.target.kind === \"storm\"",
            "stormTarget",
        ):
            self.assertIn(token, script)

        self.assertEqual(
            {
                "assets/ship-decal.png",
                "assets/asteroid-ore-glow.png",
                "assets/station-dock-panel.png",
                "assets/pirate-marker.png",
                "assets/arcade-title-card.png",
            },
            manifest_paths,
        )
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*convoy[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*beacon[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*storm[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*anchor[^"\'\)\s]*\.png')

    def test_knife_wake_visuals_are_procedural_and_reuse_existing_pirate_asset_only(self) -> None:
        script = source_text("void-prospector.js")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_paths = {asset["path"].removeprefix("games/void-prospector/") for asset in manifest["assets"]}

        for token in (
            "createInterdictionMesh",
            "syncInterdictionMeshes",
            "interdictionMeshes",
            "new THREE.ConeGeometry",
            "new THREE.LineSegments",
            "new THREE.OctahedronGeometry",
            "new THREE.TetrahedronGeometry",
            "state.target.kind === \"interdiction\"",
            "interdictionTarget",
            "interdictionRows",
        ):
            self.assertIn(token, script)

        self.assertIn("assets/pirate-marker.png", manifest_paths)
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*interdiction[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*distress[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*decoy[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*patrol[^"\'\)\s]*\.png')

    def test_signal_gate_visuals_are_procedural_and_keep_raster_manifest_local(self) -> None:
        script = source_text("void-prospector.js")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_paths = {asset["path"].removeprefix("games/void-prospector/") for asset in manifest["assets"]}

        for token in (
            "createSignalGateMesh",
            "syncSignalGateMeshes",
            "signalGateMeshes",
            "new THREE.IcosahedronGeometry",
            "new THREE.CylinderGeometry",
            "new THREE.TorusGeometry",
            "new THREE.SphereGeometry",
            "new THREE.BufferGeometry().setFromPoints",
            "state.target.kind === \"signal-gate\"",
            "signalTarget",
            "signalRows",
        ):
            self.assertIn(token, script)

        self.assertEqual(
            {
                "assets/ship-decal.png",
                "assets/asteroid-ore-glow.png",
                "assets/station-dock-panel.png",
                "assets/pirate-marker.png",
                "assets/arcade-title-card.png",
            },
            manifest_paths,
        )
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*gate[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*capacitor[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*transit[^"\'\)\s]*\.png')
        self.assertNotRegex(script, r'assets/[^"\'\)\s]*jam[^"\'\)\s]*\.png')

    def test_game_data_exposes_asset_manifest_paths_for_state_checks(self) -> None:
        assets = json.loads(self.run_node("game.GAME_DATA.assets"))

        self.assertEqual("assets/asset-manifest.json", assets["sourceManifest"])
        self.assertEqual("assets/ship-decal.png", assets["shipDecal"])
        self.assertEqual("assets/asteroid-ore-glow.png", assets["asteroidOreGlow"])
        self.assertEqual("assets/station-dock-panel.png", assets["stationDockPanel"])
        self.assertEqual("assets/pirate-marker.png", assets["pirateMarker"])
        self.assertEqual("assets/arcade-title-card.png", assets["arcadeTitleCard"])

    def run_node(self, expression: str) -> str:
        result = subprocess.run(
            [
                "node",
                "-e",
                textwrap.dedent(
                    f"""
                    const game = require("./games/void-prospector/void-prospector.js");
                    console.log(JSON.stringify({expression}));
                    """
                ),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def run_node_script(self, script: str) -> str:
        result = subprocess.run(
            [
                "node",
                "-e",
                "const game = require('./games/void-prospector/void-prospector.js');\n"
                + textwrap.dedent(script),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout


if __name__ == "__main__":
    unittest.main()
