import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VoidProspectorBeaconConvoyTests(unittest.TestCase):
    def test_convoy_route_generation_adds_v030_state_without_replacing_salvage(self) -> None:
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
              },
            });
            const targeted = game.setTarget(rift, "convoy", "convoy-rift-relay");
            console.log(JSON.stringify({
              ladderVersion: rift.ladder.version,
              salvageVersion: rift.salvage.version,
              convoyVersion: rift.convoy.version,
              convoyLabel: rift.convoy.releaseLabel,
              stormVersion: rift.storm.version,
              stormChartIds: game.stormSummary(rift).charts.map((chart) => chart.id),
              interdictionVersion: rift.interdiction.version,
              interdictionCellIds: game.interdictionSummary(rift).cells.map((cell) => cell.id),
              riftRoute: game.convoySummary(rift).routes[0],
              umbraRoute: game.convoySummary(umbra).routes[0],
              target: game.targetSummary(targeted),
              routeCount: game.createConvoyRoutes(52, game.sectorById("umbra-trench")).length +
                game.createConvoyRoutes(44, game.sectorById("rift-shelf")).length,
            }));
            """
        )

        self.assertEqual("0.1.0", result["ladderVersion"])
        self.assertEqual("0.2.0", result["salvageVersion"])
        self.assertEqual("0.3.0", result["convoyVersion"])
        self.assertEqual("Beacon Convoy", result["convoyLabel"])
        self.assertEqual("0.4.0", result["stormVersion"])
        self.assertEqual("0.5.0", result["interdictionVersion"])
        self.assertIn("storm-rift-breaker", result["stormChartIds"])
        self.assertIn("cell-rift-decoy-net", result["interdictionCellIds"])
        self.assertGreaterEqual(result["routeCount"], 2)
        self.assertEqual("convoy-rift-relay", result["riftRoute"]["id"])
        self.assertFalse(result["riftRoute"]["prerequisitesReady"])
        self.assertIn("scan anomaly-rift-lens", result["riftRoute"]["missingPrerequisites"])
        self.assertEqual("undeployed", result["riftRoute"]["beacon"]["status"])
        self.assertGreater(result["riftRoute"]["cargoValue"], 200)
        self.assertGreater(result["riftRoute"]["convoy"]["escortIntegrity"], 0)
        self.assertGreater(result["riftRoute"]["convoy"]["ambushPressure"], 0)
        self.assertGreater(result["riftRoute"]["convoy"]["hazardExposure"], 0)
        self.assertGreater(result["riftRoute"]["convoy"]["payoutCredits"], 0)
        self.assertIn("recover salvage-umbra-blackbox", result["umbraRoute"]["missingPrerequisites"])
        self.assertEqual("convoy", result["target"]["kind"])
        self.assertEqual("beacon-rift-relay", result["target"]["beaconId"])

    def test_beacon_prerequisites_deploy_maintenance_start_and_progress_are_deterministic(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            let state = game.createInitialState({
              seed: 44,
              sectorId: "rift-shelf",
              ladder: {
                currentSectorId: "rift-shelf",
                recommendedSectorId: "rift-shelf",
                unlockedSectorIds: ["spoke-approach", "rift-shelf"],
                completedSectorIds: ["spoke-approach"],
              },
            });
            const anomaly = state.anomalies.find((node) => node.id === "anomaly-rift-lens");
            state.ship.position = { ...anomaly.position };
            state = game.setTarget(state, "anomaly", anomaly.id);
            state = game.scanTarget(state, 2);
            state = game.scanTarget(state, 1);
            const ready = game.convoyRouteReadiness(state, "convoy-rift-relay");

            const route = state.convoyRoutes[0];
            state.ship.position = { ...route.beacon.position };
            state = game.setTarget(state, "convoy", route.id);
            state = game.deployRouteBeacon(state, route.id);
            state.hazard.exposure = 2;
            state.convoyRoutes[0].beaconState.integrity = 32;
            const damagedBeacon = game.convoySummary(state).routes[0].beacon.integrity;
            state = game.maintainRouteBeacon(state, route.id);
            const maintained = game.convoySummary(state).routes[0];
            state = game.startConvoyRoute(state, route.id);
            const started = game.convoySummary(state).routes[0];
            state.ship.position = { ...state.convoyRoutes[0].convoyState.position };
            state = game.advanceConvoyRoute(state, 1);
            const advanced = game.convoySummary(state).routes[0];
            console.log(JSON.stringify({
              ready,
              target: game.targetSummary(state),
              damagedBeacon,
              maintained,
              started,
              advanced,
              activeRouteId: state.convoy.activeRouteId,
              piratePressure: state.pirate.pressure,
              hazardExposure: state.hazard.exposure,
              stats: state.stats,
            }));
            """
        )

        self.assertTrue(result["ready"]["canDeployBeacon"])
        self.assertEqual("convoy", result["target"]["kind"])
        self.assertTrue(result["maintained"]["beacon"]["deployed"])
        self.assertEqual("maintained", result["maintained"]["beacon"]["status"])
        self.assertGreater(result["maintained"]["beacon"]["integrity"], result["damagedBeacon"])
        self.assertEqual("enroute", result["started"]["convoy"]["status"])
        self.assertEqual("convoy-rift-relay", result["activeRouteId"])
        self.assertGreater(result["advanced"]["convoy"]["progress"], 0)
        self.assertLess(result["advanced"]["convoy"]["escortIntegrity"], result["advanced"]["convoy"]["maxEscortIntegrity"])
        self.assertGreater(result["piratePressure"], 0)
        self.assertGreater(result["hazardExposure"], 0)
        self.assertEqual(1, result["stats"]["convoyBeaconsDeployed"])
        self.assertEqual(1, result["stats"]["convoysStarted"])

    def test_station_convoy_support_and_countermeasure_change_risk_and_reward(self) -> None:
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
            function startReadyState(options = {}) {
              let state = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder, ...options });
              const route = state.convoyRoutes[0];
              state.ship.position = { ...route.beacon.position };
              state = game.deployRouteBeacon(state, route.id);
              return game.startConvoyRoute(state, route.id);
            }

            const baseline = startReadyState();
            let supported = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder, credits: 320 });
            supported.ship.position = { ...supported.station.position };
            supported = game.purchaseStationService(supported, "escort-drones");
            supported = game.purchaseStationService(supported, "signal-jammers");
            const purchased = supported.stationServices.purchased.slice();
            supported.ship.position = { ...supported.convoyRoutes[0].beacon.position };
            supported = game.deployRouteBeacon(supported, "convoy-rift-relay");
            supported = game.startConvoyRoute(supported, "convoy-rift-relay");
            const supportedStart = game.convoySummary(supported).routes[0];
            supported = game.deployConvoyCountermeasure(supported);
            const afterBurst = game.convoySummary(supported).routes[0];
            supported.ship.position = { ...supported.convoyRoutes[0].convoyState.position };
            for (let index = 0; index < 4; index += 1) {
              supported.ship.position = { ...supported.convoyRoutes[0].convoyState.position };
              supported = game.advanceConvoyRoute(supported, 1);
            }
            const delivered = game.convoySummary(supported);
            console.log(JSON.stringify({
              purchased,
              baselineStart: game.convoySummary(baseline).routes[0],
              supportedStart,
              afterBurst,
              chargesAfterBurst: supported.stationServices.countermeasureCharges,
              delivered,
              credits: supported.credits,
              stats: supported.stats,
            }));
            """
        )

        self.assertEqual(["escort-drones", "signal-jammers"], result["purchased"])
        self.assertGreater(
            result["supportedStart"]["convoy"]["maxEscortIntegrity"],
            result["baselineStart"]["convoy"]["maxEscortIntegrity"],
        )
        self.assertLess(
            result["supportedStart"]["convoy"]["ambushPressure"],
            result["baselineStart"]["convoy"]["ambushPressure"],
        )
        self.assertTrue(result["afterBurst"]["convoy"]["countermeasureUsed"])
        self.assertLess(result["afterBurst"]["convoy"]["ambushPressure"], result["supportedStart"]["convoy"]["ambushPressure"])
        self.assertEqual(0, result["chargesAfterBurst"])
        self.assertEqual("delivered", result["delivered"]["routes"][0]["convoy"]["status"])
        self.assertGreater(result["delivered"]["payoutBanked"], result["baselineStart"]["convoy"]["payoutCredits"])
        self.assertGreaterEqual(result["credits"], 400)
        self.assertEqual(1, result["stats"]["convoyCountermeasures"])

    def test_partial_and_failure_resolution_update_ladder_and_convoy_ledger(self) -> None:
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
            function startRoute() {
              let state = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder });
              const route = state.convoyRoutes[0];
              state.ship.position = { ...route.beacon.position };
              state = game.deployRouteBeacon(state, route.id);
              return game.startConvoyRoute(state, route.id);
            }

            let partial = startRoute();
            partial.convoyRoutes[0].convoyState.escortIntegrity = 35;
            partial.convoyRoutes[0].convoyState.progress = 0.99;
            partial.ship.position = { ...partial.convoyRoutes[0].convoyState.position };
            partial = game.advanceConvoyRoute(partial, 1);

            let failed = startRoute();
            failed.convoyRoutes[0].convoyState.escortIntegrity = 17;
            failed = game.resolveConvoyPayout(failed, "convoy-rift-relay");

            console.log(JSON.stringify({
              partial: game.convoySummary(partial),
              partialCredits: partial.credits,
              partialContractConvoy: partial.contract.deliveredConvoyValue,
              partialLadder: partial.ladder,
              partialStats: partial.stats,
              failed: game.convoySummary(failed),
              failedCredits: failed.credits,
              failedStats: failed.stats,
            }));
            """
        )

        self.assertEqual("partial", result["partial"]["routes"][0]["convoy"]["status"])
        self.assertIn("convoy-rift-relay", result["partial"]["partialRouteIds"])
        self.assertIn("convoy-rift-relay", result["partial"]["completedRouteIds"])
        self.assertGreater(result["partialCredits"], 0)
        self.assertEqual(result["partialCredits"], result["partialContractConvoy"])
        self.assertIn("convoy-rift-relay", result["partialLadder"]["completedConvoyRouteIds"])
        self.assertGreater(result["partialLadder"]["convoyScore"], 0)
        self.assertEqual(1, result["partialStats"]["convoyPartialPayouts"])
        self.assertEqual("failed", result["failed"]["routes"][0]["convoy"]["status"])
        self.assertIn("convoy-rift-relay", result["failed"]["failedRouteIds"])
        self.assertEqual(0, result["failedCredits"])
        self.assertEqual(1, result["failedStats"]["convoyFailures"])

    def test_umbra_route_prerequisites_consume_hazard_chart_and_salvage_manifest(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            let state = game.createInitialState({
              seed: 52,
              sectorId: "umbra-trench",
              ladder: {
                currentSectorId: "umbra-trench",
                recommendedSectorId: "umbra-trench",
                unlockedSectorIds: ["spoke-approach", "rift-shelf", "umbra-trench"],
                completedSectorIds: ["spoke-approach", "rift-shelf"],
              },
              stationServices: { purchased: ["salvage-rig", "recovery-drones"] },
            });
            const initial = game.convoyRouteReadiness(state, "convoy-umbra-blackbox");

            const pylon = state.anomalies.find((node) => node.id === "anomaly-black-pylon");
            state.ship.position = { ...pylon.position };
            state = game.setTarget(state, "anomaly", pylon.id);
            state = game.scanTarget(state, 2);
            state = game.scanTarget(state, 2);
            const afterChart = game.convoyRouteReadiness(state, "convoy-umbra-blackbox");

            const blackbox = state.salvageSites.find((site) => site.id === "salvage-umbra-blackbox");
            state.ship.position = { ...blackbox.position };
            state = game.setTarget(state, "salvage", blackbox.id);
            for (let index = 0; index < 3; index += 1) {
              state = game.scanSalvageTarget(state, 1);
            }
            for (let index = 0; index < 3; index += 1) {
              state = game.extractSalvageTarget(state, 1);
            }
            const afterManifest = game.convoyRouteReadiness(state, "convoy-umbra-blackbox");
            state.ship.position = { ...state.convoyRoutes[0].beacon.position };
            state = game.deployRouteBeacon(state, "convoy-umbra-blackbox");
            console.log(JSON.stringify({
              initial,
              afterChart,
              afterManifest,
              manifestIds: state.ladder.salvageManifestIds,
              scannedAnomalyIds: state.ladder.scannedAnomalyIds,
              hazardCharts: state.ladder.hazardCharts,
              route: game.convoySummary(state).routes[0],
            }));
            """
        )

        self.assertIn("scan anomaly-black-pylon", result["initial"]["missing"])
        self.assertIn("recover salvage-umbra-blackbox", result["initial"]["missing"])
        self.assertIn("chart Umbra Trench", result["initial"]["missing"])
        self.assertEqual(["recover salvage-umbra-blackbox"], result["afterChart"]["missing"])
        self.assertTrue(result["afterManifest"]["ready"])
        self.assertIn("salvage-umbra-blackbox", result["manifestIds"])
        self.assertIn("anomaly-black-pylon", result["scannedAnomalyIds"])
        self.assertTrue(result["hazardCharts"]["umbra-trench"])
        self.assertTrue(result["route"]["beacon"]["deployed"])
        self.assertEqual("ready", result["route"]["convoy"]["status"])

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
