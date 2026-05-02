import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VoidProspectorKnifeWakeInterdictionTests(unittest.TestCase):
    def test_interdiction_generation_adds_v050_state_without_replacing_storm(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const rift = game.createInitialState({
              seed: 44,
              sectorId: "rift-shelf",
              ladder: {
                currentSectorId: "rift-shelf",
                recommendedSectorId: "rift-shelf",
                unlockedSectorIds: ["spoke-approach", "rift-shelf"],
                completedSectorIds: ["spoke-approach"],
                scannedAnomalyIds: ["anomaly-rift-lens"],
              },
            });
            const umbra = game.createInitialState({
              seed: 52,
              sectorId: "umbra-trench",
              ladder: {
                currentSectorId: "umbra-trench",
                recommendedSectorId: "umbra-trench",
                unlockedSectorIds: ["spoke-approach", "rift-shelf", "umbra-trench"],
                completedSectorIds: ["spoke-approach", "rift-shelf"],
                scannedAnomalyIds: ["anomaly-black-pylon"],
                salvageManifestIds: ["salvage-umbra-blackbox"],
                hazardCharts: { "umbra-trench": true },
              },
            });
            const target = game.setTarget(rift, "interdiction", "cell-rift-decoy-net");
            console.log(JSON.stringify({
              stormVersion: rift.storm.version,
              interdictionVersion: rift.interdiction.version,
              signalGateVersion: rift.signalGate.version,
              interdictionLabel: rift.interdiction.releaseLabel,
              signalGateIds: game.signalGateSummary(rift).gates.map((gate) => gate.id),
              riftCell: game.interdictionSummary(rift).cells[0],
              umbraCell: game.interdictionSummary(umbra).cells[0],
              target: game.targetSummary(target),
              generatedCount:
                game.createInterdictionCells(44, game.sectorById("rift-shelf")).length +
                game.createInterdictionCells(52, game.sectorById("umbra-trench")).length,
            }));
            """
        )

        self.assertEqual("0.4.0", result["stormVersion"])
        self.assertEqual("0.5.0", result["interdictionVersion"])
        self.assertEqual("0.6.0", result["signalGateVersion"])
        self.assertEqual("Knife Wake Interdiction", result["interdictionLabel"])
        self.assertIn("gate-rift-relay-aperture", result["signalGateIds"])
        self.assertGreaterEqual(result["generatedCount"], 2)
        self.assertEqual("cell-rift-decoy-net", result["riftCell"]["id"])
        self.assertEqual("false distress ping on the Rift Relay Convoy lane", result["riftCell"]["trigger"])
        self.assertIn("deploy convoy-rift-relay beacon", result["riftCell"]["missingPrerequisites"])
        self.assertGreater(result["riftCell"]["raidPressure"], 0)
        self.assertGreater(result["riftCell"]["rewardCredits"], 0)
        self.assertEqual(3, result["riftCell"]["responseWindow"]["opensAt"])
        self.assertGreater(result["riftCell"]["responseWindow"]["closesAt"], result["riftCell"]["responseWindow"]["opensAt"])
        self.assertIn("convoy-rift-relay", result["riftCell"]["targets"]["convoyRouteIds"])
        self.assertIn("salvage-rift-hulk", result["riftCell"]["targets"]["salvageSiteIds"])
        self.assertIn("storm-rift-breaker", result["riftCell"]["targets"]["stormChartIds"])
        self.assertTrue(result["umbraCell"]["prerequisitesReady"])
        self.assertEqual("interdiction", result["target"]["kind"])
        self.assertEqual("raider-cell", result["target"]["family"])
        self.assertIn("transponder", result["target"]["status"])

    def test_transponder_decoy_lure_and_resolution_couple_convoy_salvage_and_log(self) -> None:
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

            let unresolved = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder });
            unresolved.ship.position = { ...unresolved.convoyRoutes[0].beacon.position };
            unresolved = game.deployRouteBeacon(unresolved, "convoy-rift-relay");
            const baselineRisk = game.salvageRisk(
              unresolved.salvageSites.find((site) => site.id === "salvage-rift-hulk"),
              unresolved
            );
            unresolved = game.startConvoyRoute(unresolved, "convoy-rift-relay");
            const unresolvedRoute = game.convoySummary(unresolved).routes[0];

            let state = game.createInitialState({
              seed: 44,
              sectorId: "rift-shelf",
              ladder,
              stationServices: { purchased: ["decoy-burst"] },
            });
            state.ship.position = { ...state.convoyRoutes[0].beacon.position };
            state = game.deployRouteBeacon(state, "convoy-rift-relay");
            state = game.setTarget(state, "interdiction", "cell-rift-decoy-net");
            state.ship.position = { ...state.interdictionCells[0].position };
            state = game.scanInterdictionTransponder(state, "cell-rift-decoy-net", 2);
            state = game.scanInterdictionTransponder(state, "cell-rift-decoy-net", 1);
            state = game.placeInterdictionMarker(state, "cell-rift-decoy-net", "decoy");
            state = game.deployInterdictionLure(state, "cell-rift-decoy-net");
            state.elapsed = 4;
            state.tick = 4;
            state = game.resolveInterdictionRaid(state, "cell-rift-decoy-net", "escort");
            const resolvedRisk = game.salvageRisk(
              state.salvageSites.find((site) => site.id === "salvage-rift-hulk"),
              state
            );
            state = game.startConvoyRoute(state, "convoy-rift-relay");
            const resolvedRoute = game.convoySummary(state).routes[0];
            console.log(JSON.stringify({
              interdiction: game.interdictionSummary(state),
              baselineRisk,
              resolvedRisk,
              unresolvedRoute,
              resolvedRoute,
              charges: state.stationServices.countermeasureCharges,
              pressure: state.pirate.pressure,
              stats: state.stats,
              salvage: game.salvageSummary(state).sites.find((site) => site.id === "salvage-rift-hulk"),
              target: game.targetSummary(state),
              log: state.log.slice(0, 6).map((entry) => entry.message),
            }));
            """
        )

        self.assertEqual("success", result["interdiction"]["cells"][0]["state"]["outcome"])
        self.assertIn("cell-rift-decoy-net", result["interdiction"]["completedCellIds"])
        self.assertIn("cell-rift-decoy-net", result["interdiction"]["scannedCellIds"])
        self.assertIn("cell-rift-decoy-net", result["interdiction"]["luredCellIds"])
        self.assertEqual(1, result["interdiction"]["markersPlaced"])
        self.assertEqual(1, result["interdiction"]["luresDeployed"])
        self.assertEqual(0, result["charges"])
        self.assertLess(result["resolvedRisk"], result["baselineRisk"])
        self.assertEqual("protected", result["salvage"]["interdictionShield"]["status"])
        self.assertLess(
            result["resolvedRoute"]["convoy"]["ambushPressure"],
            result["unresolvedRoute"]["convoy"]["ambushPressure"],
        )
        self.assertGreater(
            result["resolvedRoute"]["convoy"]["escortIntegrity"],
            result["unresolvedRoute"]["convoy"]["escortIntegrity"],
        )
        self.assertEqual("cell-rift-decoy-net success", result["resolvedRoute"]["convoy"]["interdictionStatus"])
        self.assertEqual(1, result["stats"]["interdictionTranspondersScanned"])
        self.assertEqual(1, result["stats"]["interdictionMarkersPlaced"])
        self.assertEqual(1, result["stats"]["interdictionLuresDeployed"])
        self.assertEqual(1, result["stats"]["interdictionRaidsResolved"])
        self.assertGreater(result["stats"]["interdictionPayouts"], 0)
        self.assertTrue(any("Knife Wake" in entry for entry in result["log"]))

    def test_station_patrol_support_distress_marker_and_partial_failure_are_distinct(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const ladder = {
              currentSectorId: "umbra-trench",
              recommendedSectorId: "umbra-trench",
              unlockedSectorIds: ["spoke-approach", "rift-shelf", "umbra-trench"],
              completedSectorIds: ["spoke-approach", "rift-shelf"],
              scannedAnomalyIds: ["anomaly-black-pylon"],
              salvageManifestIds: ["salvage-umbra-blackbox"],
              hazardCharts: { "umbra-trench": true },
            };

            let unsupported = game.createInitialState({ seed: 52, sectorId: "umbra-trench", ladder });
            unsupported.ship.position = { ...unsupported.interdictionCells[0].position };
            unsupported = game.scanInterdictionTransponder(unsupported, "cell-umbra-blackbox-raid", 2);
            unsupported = game.scanInterdictionTransponder(unsupported, "cell-umbra-blackbox-raid", 2);
            unsupported.interdictionCells[0].interdictionState.raidPressure = 70;
            unsupported.elapsed = 6;
            unsupported.tick = 6;
            unsupported.cargo.ore = 2;
            unsupported.cargo.value = 120;
            unsupported = game.resolveInterdictionRaid(unsupported, "cell-umbra-blackbox-raid", "cargo-sacrifice");

            let supported = game.createInitialState({ seed: 52, sectorId: "umbra-trench", ladder, credits: 500 });
            supported.ship.position = { ...supported.station.position };
            supported = game.purchaseStationService(supported, "patrol-uplink");
            supported.ship.position = { ...supported.interdictionCells[0].position };
            supported = game.scanInterdictionTransponder(supported, "cell-umbra-blackbox-raid", 2);
            const supportedScan = game.interdictionSummary(supported).cells[0];
            supported = game.scanInterdictionTransponder(supported, "cell-umbra-blackbox-raid", 1);
            supported = game.placeInterdictionMarker(supported, "cell-umbra-blackbox-raid", "distress");
            supported.elapsed = 6;
            supported.tick = 6;
            supported = game.resolveInterdictionRaid(supported, "cell-umbra-blackbox-raid", "escort");
            console.log(JSON.stringify({
              unsupported: {
                interdiction: game.interdictionSummary(unsupported),
                hull: unsupported.ship.hull,
                fuel: unsupported.ship.fuel,
                cargo: unsupported.cargo,
                salvage: game.salvageSummary(unsupported).sites.find((site) => site.id === "salvage-umbra-blackbox"),
                stats: unsupported.stats,
              },
              supported: {
                purchased: supported.stationServices.purchased,
                scan: supportedScan,
                interdiction: game.interdictionSummary(supported),
                credits: supported.credits,
                ladder: supported.ladder,
                contract: supported.contract,
                stats: supported.stats,
              },
            }));
            """
        )

        self.assertEqual("partial", result["unsupported"]["interdiction"]["cells"][0]["state"]["outcome"])
        self.assertLess(result["unsupported"]["hull"], 100)
        self.assertLess(result["unsupported"]["cargo"]["ore"], 2)
        self.assertIn("cell-umbra-blackbox-raid", result["unsupported"]["interdiction"]["partialCellIds"])
        self.assertEqual(2, result["unsupported"]["stats"]["interdictionCargoLost"])

        self.assertEqual(["patrol-uplink"], result["supported"]["purchased"])
        self.assertGreater(result["supported"]["interdiction"]["scanPower"], 1)
        self.assertGreater(result["supported"]["scan"]["responseWindow"]["closesAt"], 18)
        self.assertEqual("success", result["supported"]["interdiction"]["cells"][0]["state"]["outcome"])
        self.assertIn("cell-umbra-blackbox-raid", result["supported"]["ladder"]["completedInterdictionCellIds"])
        self.assertGreater(result["supported"]["contract"]["deliveredInterdictionPayout"], 0)
        self.assertGreater(result["supported"]["credits"], 300)
        self.assertEqual(1, result["supported"]["stats"]["interdictionRaidsResolved"])

    def test_tempest_patrol_net_extends_late_run_contract_and_reset_carryover(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const ladder = {
              currentSectorId: "tempest-verge",
              recommendedSectorId: "tempest-verge",
              unlockedSectorIds: ["spoke-approach", "rift-shelf", "umbra-trench", "tempest-verge"],
              completedSectorIds: ["spoke-approach", "rift-shelf", "umbra-trench"],
            };
            let state = game.createInitialState({
              seed: 77,
              sectorId: "tempest-verge",
              ladder,
              stationServices: { purchased: ["patrol-uplink"] },
            });
            const eye = state.anomalies.find((node) => node.id === "anomaly-tempest-eye");
            state.ship.position = { ...eye.position };
            state = game.setTarget(state, "anomaly", eye.id);
            state = game.scanTarget(state, 2);
            state = game.scanTarget(state, 2);
            state = game.setTarget(state, "interdiction", "cell-tempest-patrol-net");
            state.ship.position = { ...state.interdictionCells[0].position };
            state = game.scanInterdictionTransponder(state, "cell-tempest-patrol-net", 2);
            state = game.scanInterdictionTransponder(state, "cell-tempest-patrol-net", 2);
            state = game.placeInterdictionMarker(state, "cell-tempest-patrol-net", "distress");
            state = game.deployInterdictionLure(state, "cell-tempest-patrol-net");
            state.elapsed = 8;
            state.tick = 8;
            state = game.resolveInterdictionRaid(state, "cell-tempest-patrol-net", "escort");
            const afterPatrol = JSON.parse(JSON.stringify(state));
            const reset = game.resetRun(state);
            console.log(JSON.stringify({
              contract: afterPatrol.contract,
              interdiction: game.interdictionSummary(afterPatrol),
              ladder: afterPatrol.ladder,
              resetInterdiction: game.interdictionSummary(reset),
              resetLadder: reset.ladder,
            }));
            """
        )

        self.assertEqual(1, result["contract"]["requiredInterdictions"])
        self.assertEqual(1, result["contract"]["deliveredInterdictions"])
        self.assertGreaterEqual(result["contract"]["deliveredInterdictionPayout"], 180)
        self.assertEqual("success", result["interdiction"]["cells"][0]["state"]["outcome"])
        self.assertIn("cell-tempest-patrol-net", result["ladder"]["completedInterdictionCellIds"])
        self.assertGreater(result["ladder"]["interdictionScore"], 0)
        self.assertIn("cell-tempest-patrol-net", result["resetLadder"]["completedInterdictionCellIds"])
        self.assertEqual("0.5.0", result["resetInterdiction"]["version"])

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
