import json
import re
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "void-prospector"
MANIFEST_PATH = GAME_DIR / "assets" / "asset-manifest.json"


def read_game_file(name: str) -> str:
    return (GAME_DIR / name).read_text(encoding="utf-8")


class VoidProspectorSurveySurfaceTests(unittest.TestCase):
    def test_direct_page_exposes_survey_ladder_ui_hooks(self) -> None:
        html = read_game_file("index.html")

        for hook in (
            "ladder-readout",
            "sector-readout",
            "hazard-readout",
            "scan-readout",
            "salvage-readout",
            "convoy-readout",
            "beacon-readout",
            "ambush-readout",
            "service-readout",
            "scan-action",
            "beacon-action",
            "convoy-action",
            "abandon-action",
            "salvage-target-family",
            "salvage-lock-state",
            "salvage-extraction-state",
            "salvage-risk-reward",
            "convoy-route-state",
            "convoy-beacon-state",
            "convoy-escort-state",
            "convoy-risk-state",
            "convoy-reward-state",
            "convoy-support-state",
            "survey-panel",
            "ladder-title",
            "ladder-status-surface",
            "sector-list",
            "convoy-list",
            "sector-select",
            "sector-action",
            "service-probes-action",
            "service-decoy-action",
            "service-salvage-rig-action",
            "service-recovery-drones-action",
            "service-escort-action",
            "service-jammers-action",
            "countermeasure-action",
            "event-log",
        ):
            self.assertIn(hook, html)

        self.assertIn("v0.3.0 Beacon Convoy", html)
        self.assertIn("C scan or lock", html)
        self.assertIn("Space/M mine or extract", html)
        self.assertIn('aria-label="Survey Ladder controls"', html)
        self.assertIn('aria-label="Selected salvage target state"', html)
        self.assertIn('aria-label="Selected convoy route state"', html)
        self.assertIn('aria-label="Convoy route state"', html)

    def test_survey_surface_css_keeps_desktop_and_narrow_layout_contracts(self) -> None:
        css = read_game_file("void-prospector.css")

        for token in (
            ".survey-panel",
            ".sector-list",
            ".sector-row",
            ".choice-row",
            ".service-panel",
            ".salvage-target-data",
            ".convoy-target-data",
            ".convoy-list",
            ".convoy-row",
            ".event-log",
            "max-height: calc(100vh - 96px)",
            "max-height: min(170px, max(150px, calc(100vh - 550px)))",
            "overflow: auto",
            "grid-template-columns: repeat(auto-fit, minmax(96px, 1fr))",
            "@media (max-height: 700px) and (min-width: 981px)",
            "@media (max-width: 980px)",
            "@media (max-width: 640px)",
        ):
            self.assertIn(token, css)

        self.assertRegex(css, r"\.survey-panel\s*\{[^}]*position: fixed")
        self.assertRegex(css, r"\.target-panel\s*\{[^}]*max-height: calc\(100vh - 96px\)")
        self.assertRegex(css, r"@media \(max-height: 700px\) and \(min-width: 981px\)[\s\S]*?\.survey-panel\s*\{[^}]*position: relative")
        self.assertRegex(css, r"@media \(max-width: 980px\)[\s\S]*?\.survey-panel\s*\{[^}]*position: relative")
        self.assertRegex(css, r"@media \(max-width: 980px\)[\s\S]*?\.target-panel\s*\{[^}]*position: relative")
        self.assertIn("width: calc(100vw - 24px)", css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", css)
        self.assertNotIn("border-radius: 12px", css)
        self.assertNotIn("overflow-x: scroll", css)

    def test_cockpit_surface_models_route_objective_hazard_and_actions(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const ladder = {
              currentSectorId: "spoke-approach",
              recommendedSectorId: "rift-shelf",
              unlockedSectorIds: ["spoke-approach", "rift-shelf"],
              completedSectorIds: ["spoke-approach"],
            };
            let state = game.createInitialState({ seed: 9, ladder });
            state = game.stepSpaceflight(state, {}, 1);
            const surface = game.surveyCockpitSurface(state);
            const chosen = game.chooseSector(state, "rift-shelf");
            const anomaly = chosen.anomalies[0];
            const anomalyTarget = game.setTarget(chosen, "anomaly", anomaly.id);
            const anomalySurface = game.surveyCockpitSurface(anomalyTarget);
            console.log(JSON.stringify({
              titleText: surface.titleText,
              ladderText: surface.ladderText,
              routeText: surface.routeText,
              sectorStates: surface.sectors.map((sector) => [sector.id, sector.state, sector.unlocked]),
              canSetSectorAfterIdleTick: surface.actions.canSetSector,
              chosenSector: chosen.ladder.currentSectorId,
              chosenHazard: chosen.hazard.intensity,
              chosenObjective: game.surveyCockpitSurface(chosen).objectiveProgressText,
              canScanAnomaly: anomalySurface.actions.canScan,
              anomalyScanText: anomalySurface.scanText,
            }));
            """
        )

        self.assertIn("Survey Ladder", result["titleText"])
        self.assertIn("tier 1", result["ladderText"])
        self.assertIn("Rift Shelf", result["routeText"])
        self.assertIn(["spoke-approach", "current", True], result["sectorStates"])
        self.assertIn(["rift-shelf", "recommended", True], result["sectorStates"])
        self.assertIn(["umbra-trench", "locked", False], result["sectorStates"])
        self.assertTrue(result["canSetSectorAfterIdleTick"])
        self.assertEqual("rift-shelf", result["chosenSector"])
        self.assertGreater(result["chosenHazard"], 0)
        self.assertIn("10 ore", result["chosenObjective"])
        self.assertTrue(result["canScanAnomaly"])
        self.assertIn("0/1 scans", result["anomalyScanText"])

    def test_derelict_salvage_surface_exposes_target_contract_and_recovery_support(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const ladder = {
              currentSectorId: "umbra-trench",
              recommendedSectorId: "umbra-trench",
              unlockedSectorIds: ["spoke-approach", "rift-shelf", "umbra-trench"],
              completedSectorIds: ["spoke-approach", "rift-shelf"],
            };
            let state = game.createInitialState({ seed: 52, sectorId: "umbra-trench", ladder, credits: 220 });
            state.ship.position = { ...state.station.position };
            state = game.dockAtStation(state);
            const dockSurface = game.surveyCockpitSurface(state);
            const vault = state.salvageSites.find((site) => site.id === "salvage-umbra-vault");
            state = game.setTarget(state, "salvage", vault.id);
            const targetSurface = game.surveyCockpitSurface(state);
            state.ship.position = { ...vault.position };
            state = game.scanSalvageTarget(state, 2);
            state = game.scanSalvageTarget(state, 1);
            const lockedSurface = game.surveyCockpitSurface(state);
            console.log(JSON.stringify({
              titleText: targetSurface.titleText,
              objectiveProgressText: targetSurface.objectiveProgressText,
              salvageText: targetSurface.salvageText,
              salvageTarget: targetSurface.salvageTarget,
              lockedTarget: lockedSurface.salvageTarget,
              target: game.targetSummary(state),
              services: dockSurface.services.map((service) => [service.id, service.status, service.enabled]),
              actions: targetSurface.actions,
            }));
            """
        )

        self.assertIn("Derelict Salvage v0.2.0", result["titleText"])
        self.assertIn("0/90cr salvage", result["objectiveProgressText"])
        self.assertIn("0/1 relic", result["objectiveProgressText"])
        self.assertIn("Derelict Salvage", result["salvageText"])
        self.assertIn("derelict-hull / relic / 3 units", result["salvageTarget"]["familyText"])
        self.assertIn("risk", result["salvageTarget"]["riskRewardText"])
        self.assertIn("cr", result["salvageTarget"]["riskRewardText"])
        self.assertIn("0/90cr contract", result["salvageTarget"]["contractText"])
        self.assertIn("0/1 relic", result["salvageTarget"]["contractText"])
        self.assertIn("lock 100% / locked", result["lockedTarget"]["lockText"])
        self.assertEqual("salvage", result["target"]["kind"])
        self.assertEqual("derelict-hull", result["target"]["type"])
        self.assertTrue(result["actions"]["canScanSalvage"])
        self.assertTrue(result["actions"]["canExtractSalvage"])
        self.assertTrue(result["actions"]["canAbandonSalvage"])
        self.assertIn(["salvage-rig", "80cr ready", True], result["services"])
        self.assertIn(["recovery-drones", "95cr ready", True], result["services"])

    def test_beacon_convoy_surface_exposes_route_actions_support_and_rewards(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const ladder = {
              currentSectorId: "rift-shelf",
              recommendedSectorId: "rift-shelf",
              unlockedSectorIds: ["spoke-approach", "rift-shelf"],
              completedSectorIds: ["spoke-approach"],
              scannedAnomalyIds: ["anomaly-rift-lens"],
            };
            let state = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder, credits: 320 });
            state.ship.position = { ...state.station.position };
            state = game.dockAtStation(state);
            state = game.purchaseStationService(state, "escort-drones");
            state = game.purchaseStationService(state, "signal-jammers");
            state.ship.position = { ...state.convoyRoutes[0].beacon.position };
            state = game.setTarget(state, "convoy", "convoy-rift-relay");
            const readySurface = game.surveyCockpitSurface(state);
            state = game.deployRouteBeacon(state, "convoy-rift-relay");
            const deployedSurface = game.surveyCockpitSurface(state);
            state = game.startConvoyRoute(state, "convoy-rift-relay");
            const activeSurface = game.surveyCockpitSurface(state);
            console.log(JSON.stringify({
              readyTarget: readySurface.convoyTarget,
              readyActions: readySurface.actions,
              readyRows: readySurface.convoyRows,
              deployedTarget: deployedSurface.convoyTarget,
              deployedActions: deployedSurface.actions,
              activeTarget: activeSurface.convoyTarget,
              activeActions: activeSurface.actions,
              activeRows: activeSurface.convoyRows,
              convoyText: activeSurface.convoyText,
              beaconText: activeSurface.beaconText,
              ambushText: activeSurface.ambushText,
              serviceText: activeSurface.serviceText,
              services: readySurface.services.map((service) => [service.id, service.status, service.enabled]),
            }));
            """
        )

        self.assertIn("Rift Relay Convoy / needs beacon", result["readyTarget"]["routeText"])
        self.assertIn("Rift Relay Beacon / undeployed", result["readyTarget"]["beaconText"])
        self.assertIn("ambush 31 / hazard 1.2", result["readyTarget"]["riskText"])
        self.assertIn("260cr reward", result["readyTarget"]["rewardText"])
        self.assertIn("escort +18 / ambush -24 / payout +8% / 1 burst", result["readyTarget"]["supportText"])
        self.assertTrue(result["readyActions"]["canDeployBeacon"])
        self.assertFalse(result["readyActions"]["canStartConvoy"])
        self.assertEqual("needs beacon", result["readyRows"][0]["state"])

        self.assertIn("Rift Relay Beacon / deployed", result["deployedTarget"]["beaconText"])
        self.assertTrue(result["deployedActions"]["canMaintainBeacon"])
        self.assertTrue(result["deployedActions"]["canStartConvoy"])

        self.assertIn("Rift Relay Convoy / enroute", result["activeTarget"]["routeText"])
        self.assertIn("escort 88/88", result["activeTarget"]["escortText"])
        self.assertIn("ambush 7 / hazard 1.2", result["activeTarget"]["riskText"])
        self.assertTrue(result["activeActions"]["canCountermeasureConvoy"])
        self.assertFalse(result["activeActions"]["canStartConvoy"])
        self.assertEqual("enroute", result["activeRows"][0]["state"])
        self.assertIn("Beacon Convoy / Rift Relay Convoy / enroute / escort 88/88", result["convoyText"])
        self.assertIn("Rift Relay Beacon / deployed", result["beaconText"])
        self.assertIn("ambush 7 / hazard 1.2 / 260cr", result["ambushText"])
        self.assertIn("Escort Drones + Signal Jammers / 1 burst", result["serviceText"])
        self.assertIn(["escort-drones", "installed", False], result["services"])
        self.assertIn(["signal-jammers", "installed", False], result["services"])

    def test_station_service_surface_shows_consequences_and_decoy_readiness(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const ladder = {
              currentSectorId: "rift-shelf",
              recommendedSectorId: "rift-shelf",
              unlockedSectorIds: ["spoke-approach", "rift-shelf"],
              completedSectorIds: ["spoke-approach"],
            };
            let state = game.createInitialState({ seed: 17, sectorId: "rift-shelf", ladder, credits: 180 });
            state.ship.position = { ...state.station.position };
            state = game.dockAtStation(state);
            const dockSurface = game.surveyCockpitSurface(state);
            state = game.purchaseStationService(state, "survey-probes");
            state = game.purchaseStationService(state, "decoy-burst");
            state.pirate.state = "shadowing";
            state.pirate.encounterState = "shadow";
            state.pirate.pressure = 55;
            const armedSurface = game.surveyCockpitSurface(state);
            const afterBurst = game.deployCountermeasure(state);
            console.log(JSON.stringify({
              dockServices: dockSurface.services.map((service) => [service.id, service.status, service.enabled]),
              purchasedServices: armedSurface.services.map((service) => [service.id, service.status, service.enabled]),
              serviceText: armedSurface.serviceText,
              countermeasureReady: armedSurface.actions.countermeasureReady,
              countermeasureText: armedSurface.actions.countermeasureText,
              pressureAfterBurst: afterBurst.pirate.pressure,
              chargesAfterBurst: afterBurst.stationServices.countermeasureCharges,
            }));
            """
        )

        self.assertIn(["survey-probes", "45cr ready", True], result["dockServices"])
        self.assertIn(["decoy-burst", "60cr ready", True], result["dockServices"])
        self.assertIn(["survey-probes", "installed", False], result["purchasedServices"])
        self.assertIn(["decoy-burst", "installed", False], result["purchasedServices"])
        self.assertIn("Survey Probes + Decoy Burst", result["serviceText"])
        self.assertTrue(result["countermeasureReady"])
        self.assertEqual("1 burst", result["countermeasureText"])
        self.assertEqual(20, result["pressureAfterBurst"])
        self.assertEqual(0, result["chargesAfterBurst"])

    def test_survey_surface_reuses_existing_project_local_assets_only(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_paths = {
            asset["path"].removeprefix("games/void-prospector/")
            for asset in manifest["assets"]
        }
        files = {
            "index.html": read_game_file("index.html"),
            "void-prospector.css": read_game_file("void-prospector.css"),
            "void-prospector.js": read_game_file("void-prospector.js"),
        }

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
        for filename, text in files.items():
            for reference in re.findall(r'assets/[^"\'\)\s]+\.png', text):
                self.assertIn(reference, manifest_paths, f"{filename} references {reference}")
                self.assertNotIn("://", reference)

    def run_node(self, script: str) -> dict:
        completed = subprocess.run(
            ["node", "-e", textwrap.dedent(script)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
