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
            "storm-readout",
            "interdiction-readout",
            "signal-gate-readout",
            "beacon-readout",
            "ambush-readout",
            "storm-window-readout",
            "storm-anchor-readout",
            "interdiction-raid-readout",
            "interdiction-lure-readout",
            "signal-capacitor-readout",
            "signal-transit-readout",
            "signal-jam-readout",
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
            "storm-chart-state",
            "storm-window-state",
            "storm-anchor-state",
            "storm-exposure-state",
            "storm-reward-state",
            "storm-support-state",
            "interdiction-cell-state",
            "interdiction-marker-state",
            "interdiction-window-state",
            "interdiction-exposure-state",
            "interdiction-reward-state",
            "interdiction-support-state",
            "signal-gate-state",
            "signal-pylon-state",
            "signal-capacitor-state",
            "signal-window-state",
            "signal-convoy-state",
            "signal-jam-state",
            "signal-reward-state",
            "signal-prereq-state",
            "survey-panel",
            "ladder-title",
            "ladder-status-surface",
            "sector-list",
            "convoy-list",
            "storm-list",
            "interdiction-list",
            "signal-list",
            "sector-select",
            "sector-action",
            "service-probes-action",
            "service-decoy-action",
            "service-salvage-rig-action",
            "service-recovery-drones-action",
            "service-escort-action",
            "service-jammers-action",
            "service-chart-processors-action",
            "service-storm-plating-action",
            "service-patrol-uplink-action",
            "service-gate-tuners-action",
            "countermeasure-action",
            "event-log",
        ):
            self.assertIn(hook, html)

        self.assertIn("v0.6.0 Signal Gate Expedition", html)
        self.assertIn("C scan/transponder/harmonics", html)
        self.assertIn("B beacon/anchor/marker/pylon", html)
        self.assertIn("Space/M mine or extract", html)
        self.assertIn('aria-label="Survey Ladder controls"', html)
        self.assertIn('aria-label="Selected salvage target state"', html)
        self.assertIn('aria-label="Selected convoy route state"', html)
        self.assertIn('aria-label="Selected storm chart state"', html)
        self.assertIn('aria-label="Selected interdiction cell state"', html)
        self.assertIn('aria-label="Selected signal gate state"', html)
        self.assertIn('aria-label="Convoy route state"', html)
        self.assertIn('aria-label="Storm chart state"', html)
        self.assertIn('aria-label="Knife Wake interdiction state"', html)
        self.assertIn('aria-label="Signal Gate Expedition state"', html)

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
            ".storm-target-data",
            ".interdiction-target-data",
            ".signal-target-data",
            ".convoy-list",
            ".convoy-row",
            ".storm-list",
            ".storm-row",
            ".interdiction-list",
            ".interdiction-row",
            ".signal-list",
            ".signal-row",
            ".event-log",
            "max-height: calc(100vh - 96px)",
            "max-height: min(260px, max(190px, calc(100vh - 520px)))",
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
        self.assertIn('.storm-row[data-state="window locked"]', css)
        self.assertIn('.interdiction-row[data-state="distress marker armed"]', css)
        self.assertIn('.signal-row[data-state="transit window open"]', css)
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

    def test_storm_cartography_surface_exposes_chart_anchor_window_support_and_actions(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const ladder = {
              currentSectorId: "rift-shelf",
              recommendedSectorId: "rift-shelf",
              unlockedSectorIds: ["spoke-approach", "rift-shelf"],
              completedSectorIds: ["spoke-approach"],
              scannedAnomalyIds: ["anomaly-rift-lens"],
              hazardCharts: { "rift-shelf": true },
            };
            let state = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder, credits: 500 });
            state.ship.position = { ...state.station.position };
            state = game.dockAtStation(state);
            state = game.purchaseStationService(state, "chart-processors");
            state = game.purchaseStationService(state, "storm-plating");
            state = game.purchaseStationService(state, "signal-jammers");
            state = game.setTarget(state, "storm", "storm-rift-breaker");
            state.ship.position = { ...state.stormCharts[0].position };
            const chartSurface = game.surveyCockpitSurface(state);
            state = game.scanStormChart(state, 2);
            state.ship.position = { ...state.stormCharts[0].anchor.position };
            const anchorSurface = game.surveyCockpitSurface(state);
            state = game.deployStormAnchor(state, "storm-rift-breaker");
            state.elapsed = 5;
            state.tick = 5;
            state = game.lockStormRouteWindow(state, "storm-rift-breaker");
            const lockedSurface = game.surveyCockpitSurface(state);
            console.log(JSON.stringify({
              chartTarget: chartSurface.stormTarget,
              chartActions: chartSurface.actions,
              anchorTarget: anchorSurface.stormTarget,
              anchorActions: anchorSurface.actions,
              lockedTarget: lockedSurface.stormTarget,
              lockedActions: lockedSurface.actions,
              stormText: lockedSurface.stormText,
              stormWindowText: lockedSurface.stormWindowText,
              stormAnchorText: lockedSurface.stormAnchorText,
              stormRows: lockedSurface.stormRows,
              services: lockedSurface.services.map((service) => [service.id, service.status, service.enabled]),
              contract: state.contract,
              target: game.targetSummary(state),
            }));
            """
        )

        self.assertIn("Rift Breaker Front / uncharted", result["chartTarget"]["chartText"])
        self.assertIn("opens 4s", result["chartTarget"]["windowText"])
        self.assertIn("intensity 1.8", result["chartTarget"]["exposureText"])
        self.assertIn("150cr reward", result["chartTarget"]["rewardText"])
        self.assertIn("scan +0.75", result["chartTarget"]["supportText"])
        self.assertTrue(result["chartActions"]["canScan"])

        self.assertIn("Rift Breaker Front / charted", result["anchorTarget"]["chartText"])
        self.assertTrue(result["anchorActions"]["canDeployStormAnchor"])

        self.assertIn("Storm Cartography / Rift Breaker Front / window locked", result["stormText"])
        self.assertIn("window locked", result["stormWindowText"])
        self.assertIn("Relay Anchor / deployed", result["stormAnchorText"])
        self.assertIn("reroute 0/2 salvage", result["lockedTarget"]["exposureText"])
        self.assertTrue(result["lockedActions"]["canMaintainStormAnchor"])
        self.assertTrue(result["lockedActions"]["canRerouteStormSalvage"])
        self.assertTrue(result["lockedActions"]["canCountermeasureStorm"])
        self.assertEqual("window locked", result["stormRows"][0]["state"])
        self.assertIn(["chart-processors", "installed", False], result["services"])
        self.assertIn(["storm-plating", "installed", False], result["services"])
        self.assertEqual(1, result["contract"]["deliveredStormCharts"])
        self.assertEqual("storm", result["target"]["kind"])
        self.assertEqual("deployed", result["target"]["anchorStatus"])

    def test_knife_wake_surface_exposes_cell_actions_support_and_consequences(self) -> None:
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
            let state = game.createInitialState({ seed: 48, sectorId: "rift-shelf", ladder, credits: 520 });
            state.ship.position = { ...state.station.position };
            state = game.dockAtStation(state);
            state = game.purchaseStationService(state, "patrol-uplink");
            state.ship.position = { ...state.convoyRoutes[0].beacon.position };
            state = game.deployRouteBeacon(state, "convoy-rift-relay");
            state = game.setTarget(state, "interdiction", "cell-rift-decoy-net");
            state.ship.position = { ...state.interdictionCells[0].position };
            const readySurface = game.surveyCockpitSurface(state);
            state = game.scanInterdictionTransponder(state, "cell-rift-decoy-net", 2);
            const scannedSurface = game.surveyCockpitSurface(state);
            state = game.placeInterdictionMarker(state, "cell-rift-decoy-net", "distress");
            const markerSurface = game.surveyCockpitSurface(state);
            state = game.deployInterdictionLure(state, "cell-rift-decoy-net");
            const lureSurface = game.surveyCockpitSurface(state);
            state.elapsed = 5;
            state.tick = 5;
            state = game.resolveInterdictionRaid(state, "cell-rift-decoy-net", "escort");
            const resolvedSurface = game.surveyCockpitSurface(state);
            console.log(JSON.stringify({
              readyTitle: readySurface.titleText,
              readyText: readySurface.interdictionText,
              readyTarget: readySurface.interdictionTarget,
              readyActions: readySurface.actions,
              scannedActions: scannedSurface.actions,
              markerTarget: markerSurface.interdictionTarget,
              markerRows: markerSurface.interdictionRows,
              markerActions: markerSurface.actions,
              lureTarget: lureSurface.interdictionTarget,
              lureText: lureSurface.interdictionLureText,
              resolvedText: resolvedSurface.interdictionText,
              resolvedTarget: resolvedSurface.interdictionTarget,
              resolvedLog: resolvedSurface.log,
              services: readySurface.services.map((service) => [service.id, service.status, service.enabled]),
              serviceText: readySurface.serviceText,
              target: game.targetSummary(state),
              stats: state.stats,
              contract: state.contract,
              routeStatus: state.convoyRoutes[0].convoyState.interdictionStatus,
              salvageShield: state.salvageSites[0].salvageState.interdictionShield,
            }));
            """
        )

        self.assertIn("Knife Wake Interdiction v0.5.0", result["readyTitle"])
        self.assertIn("Knife Wake Interdiction / Rift Decoy Net", result["readyText"])
        self.assertIn("Rift Decoy Net / distress lure / raider-cell", result["readyTarget"]["cellText"])
        self.assertIn("raid 28 / convoy 1 / salvage 1 / storm 1", result["readyTarget"]["exposureText"])
        self.assertIn("scan +0.85 / patrol +14 / raid -28% / window +3s / payout +10% / 1 burst", result["readyTarget"]["supportText"])
        self.assertTrue(result["readyActions"]["canScanInterdiction"])
        self.assertTrue(result["readyActions"]["canScan"])
        self.assertFalse(result["readyActions"]["canPlaceInterdictionMarker"])

        self.assertTrue(result["scannedActions"]["canPlaceInterdictionMarker"])
        self.assertTrue(result["scannedActions"]["canCountermeasureInterdiction"])
        self.assertIn("marker distress / lure no / scan yes", result["markerTarget"]["markerText"])
        self.assertIn("window marked", result["markerTarget"]["windowText"])
        self.assertEqual("distress marker armed", result["markerRows"][0]["state"])
        self.assertTrue(result["markerActions"]["canDeployInterdictionLure"])

        self.assertIn("marker distress / lure yes / scan yes", result["lureTarget"]["markerText"])
        self.assertIn("marker distress / lure yes", result["lureText"])
        self.assertIn("Rift Decoy Net / success", result["resolvedText"])
        self.assertIn("success", result["resolvedTarget"]["rewardText"])
        self.assertIn("Rift Decoy Net broken", result["resolvedLog"][0])
        self.assertIn(["patrol-uplink", "installed", False], result["services"])
        self.assertIn("Patrol Uplink", result["serviceText"])
        self.assertEqual("interdiction", result["target"]["kind"])
        self.assertEqual("success", result["target"]["outcome"])
        self.assertEqual(1, result["stats"]["interdictionTranspondersScanned"])
        self.assertEqual(1, result["stats"]["interdictionMarkersPlaced"])
        self.assertEqual(1, result["stats"]["interdictionLuresDeployed"])
        self.assertEqual(1, result["stats"]["interdictionRaidsResolved"])
        self.assertEqual(1, result["contract"]["deliveredInterdictions"])
        self.assertIn("cell-rift-decoy-net success", result["routeStatus"])
        self.assertEqual("protected", result["salvageShield"]["status"])

    def test_signal_gate_surface_exposes_gate_actions_support_and_consequences(self) -> None:
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
            let state = game.createInitialState({ seed: 64, sectorId: "rift-shelf", ladder, credits: 720 });
            state.ship.position = { ...state.station.position };
            state = game.dockAtStation(state);
            state = game.purchaseStationService(state, "gate-tuners");
            state.ship.position = { ...state.convoyRoutes[0].beacon.position };
            state = game.deployRouteBeacon(state, "convoy-rift-relay");
            state = game.setTarget(state, "signal-gate", "gate-rift-relay-aperture");
            state.ship.position = { ...state.signalGates[0].position };
            const readySurface = game.surveyCockpitSurface(state);
            state = game.scanSignalGateHarmonics(state, "gate-rift-relay-aperture", 2);
            state.ship.position = { ...state.signalGates[0].pylon.position };
            const scannedSurface = game.surveyCockpitSurface(state);
            state = game.alignSignalGatePylon(state, "gate-rift-relay-aperture");
            state.ship.position = { ...state.signalGates[0].position };
            state = game.chargeSignalGateCapacitor(state, "gate-rift-relay-aperture", 2);
            state.elapsed = 6;
            state.tick = 6;
            const chargedSurface = game.surveyCockpitSurface(state);
            state = game.commitSignalGateTransit(state, "gate-rift-relay-aperture", "convoy");
            const resolvedSurface = game.surveyCockpitSurface(state);
            console.log(JSON.stringify({
              readyTitle: readySurface.titleText,
              readyText: readySurface.signalGateText,
              readyTarget: readySurface.signalTarget,
              readyRows: readySurface.signalRows,
              readyActions: readySurface.actions,
              scannedActions: scannedSurface.actions,
              chargedTarget: chargedSurface.signalTarget,
              chargedActions: chargedSurface.actions,
              resolvedText: resolvedSurface.signalGateText,
              resolvedTarget: resolvedSurface.signalTarget,
              resolvedRows: resolvedSurface.signalRows,
              resolvedLog: resolvedSurface.log,
              serviceText: readySurface.serviceText,
              services: readySurface.services.map((service) => [service.id, service.status, service.enabled]),
              target: game.targetSummary(state),
              stats: state.stats,
              contract: state.contract,
              routeStatus: state.convoyRoutes[0].convoyState.signalGateStatus,
              routeDelivered: state.convoyRoutes[0].convoyState.deliveredValue,
              salvageShield: state.salvageSites[0].salvageState.signalGateShield,
            }));
            """
        )

        self.assertIn("Signal Gate Expedition v0.6.0", result["readyTitle"])
        self.assertIn("Signal Gate Expedition / Rift Relay Signal Gate", result["readyText"])
        self.assertIn("Rift Relay Signal Gate / relay aperture / convoy-lane", result["readyTarget"]["gateText"])
        self.assertIn("Rift Relay Pylon / unaligned", result["readyTarget"]["pylonText"])
        self.assertIn("charge 0/3.5 / harmonics no", result["readyTarget"]["capacitorText"])
        self.assertIn("opens 5s / closes 19s", result["readyTarget"]["windowText"])
        self.assertIn("convoy-rift-relay / convoy 1 / salvage 1 / storm 1", result["readyTarget"]["convoyText"])
        self.assertIn("jam 22", result["readyTarget"]["jamText"])
        self.assertIn("scan +0.9 / pylon +16 / charge +0.8 / window +3s / jam -22% / payout +12% / 1 burst", result["readyTarget"]["supportText"])
        self.assertEqual("harmonics quiet", result["readyRows"][0]["state"])
        self.assertTrue(result["readyActions"]["canScanSignalGate"])
        self.assertTrue(result["readyActions"]["canScan"])
        self.assertFalse(result["readyActions"]["canAlignSignalGatePylon"])

        self.assertTrue(result["scannedActions"]["canAlignSignalGatePylon"])
        self.assertIn("charge 3.5/3.5 / harmonics yes", result["chargedTarget"]["capacitorText"])
        self.assertTrue(result["chargedActions"]["canCommitSignalGateTransit"])
        self.assertTrue(result["chargedActions"]["canCountermeasureSignalGate"])

        self.assertIn("Rift Relay Signal Gate / success", result["resolvedText"])
        self.assertIn("success", result["resolvedTarget"]["rewardText"])
        self.assertEqual("success", result["resolvedRows"][0]["state"])
        self.assertIn("Rift Relay Signal Gate opened", result["resolvedLog"][0])
        self.assertIn("Gate Tuners / 1 burst", result["serviceText"])
        self.assertIn(["gate-tuners", "installed", False], result["services"])
        self.assertEqual("signal-gate", result["target"]["kind"])
        self.assertEqual("success", result["target"]["outcome"])
        self.assertEqual(1, result["stats"]["signalGateScans"])
        self.assertEqual(1, result["stats"]["signalPylonsAligned"])
        self.assertEqual(1, result["stats"]["signalCapacitorsCharged"])
        self.assertEqual(1, result["stats"]["signalGateTransits"])
        self.assertEqual(1, result["stats"]["signalGateConvoyTransits"])
        self.assertEqual(1, result["contract"]["deliveredSignalTransits"])
        self.assertIn("gate-rift-relay-aperture success", result["routeStatus"])
        self.assertGreater(result["routeDelivered"], 0)
        self.assertEqual("transit shielded", result["salvageShield"]["status"])

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
