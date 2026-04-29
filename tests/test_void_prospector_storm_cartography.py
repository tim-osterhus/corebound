import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VoidProspectorStormCartographyTests(unittest.TestCase):
    def test_storm_chart_generation_adds_v040_state_without_replacing_convoy(self) -> None:
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
                hazardCharts: { "rift-shelf": true },
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
            const target = game.setTarget(rift, "storm", "storm-rift-breaker");
            console.log(JSON.stringify({
              ladderVersion: rift.ladder.version,
              salvageVersion: rift.salvage.version,
              convoyVersion: rift.convoy.version,
              stormVersion: rift.storm.version,
              stormLabel: rift.storm.releaseLabel,
              riftChart: game.stormSummary(rift).charts[0],
              umbraChart: game.stormSummary(umbra).charts[0],
              target: game.targetSummary(target),
              generatedCount:
                game.createStormCharts(44, game.sectorById("rift-shelf")).length +
                game.createStormCharts(52, game.sectorById("umbra-trench")).length,
            }));
            """
        )

        self.assertEqual("0.1.0", result["ladderVersion"])
        self.assertEqual("0.2.0", result["salvageVersion"])
        self.assertEqual("0.3.0", result["convoyVersion"])
        self.assertEqual("0.4.0", result["stormVersion"])
        self.assertEqual("Storm Cartography", result["stormLabel"])
        self.assertGreaterEqual(result["generatedCount"], 2)
        self.assertEqual("storm-rift-breaker", result["riftChart"]["id"])
        self.assertTrue(result["riftChart"]["prerequisitesReady"])
        self.assertGreater(result["riftChart"]["intensity"], 1)
        self.assertEqual(4, result["riftChart"]["safeWindow"]["opensAt"])
        self.assertGreater(result["riftChart"]["safeWindow"]["closesAt"], result["riftChart"]["safeWindow"]["opensAt"])
        self.assertEqual("anchor-rift-breaker", result["riftChart"]["anchor"]["id"])
        self.assertIn("convoy-rift-relay", result["riftChart"]["modifiers"]["convoyRouteIds"])
        self.assertIn("salvage-rift-hulk", result["riftChart"]["modifiers"]["salvageSiteIds"])
        self.assertGreater(result["riftChart"]["rewardCredits"], 0)
        self.assertFalse(result["umbraChart"]["prerequisitesReady"])
        self.assertIn("scan anomaly-black-pylon", result["umbraChart"]["missingPrerequisites"])
        self.assertIn("recover salvage-umbra-blackbox", result["umbraChart"]["missingPrerequisites"])
        self.assertEqual("storm", result["target"]["kind"])
        self.assertEqual("anchor-rift-breaker", result["target"]["anchorId"])

    def test_scan_anchor_window_lock_convoy_and_salvage_reroute_are_deterministic(self) -> None:
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
            let state = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder });
            const baselineRoute = game.convoySummary(state).routes[0];
            const baselineRisk = game.salvageRisk(state.salvageSites.find((site) => site.id === "salvage-rift-hulk"), state);

            state = game.setTarget(state, "storm", "storm-rift-breaker");
            state.ship.position = { ...state.stormCharts[0].position };
            state = game.scanStormChart(state, 2);
            state = game.scanStormChart(state, 2);
            state = game.scanStormChart(state, 1);
            state.ship.position = { ...state.stormCharts[0].anchor.position };
            state = game.deployStormAnchor(state, "storm-rift-breaker");
            state.elapsed = 5;
            state.tick = 5;
            state = game.lockStormRouteWindow(state, "storm-rift-breaker");
            state = game.rerouteStormSalvage(state, "salvage-rift-hulk", "storm-rift-breaker");
            const locked = game.stormSummary(state).charts[0];
            const routedRisk = game.salvageRisk(state.salvageSites.find((site) => site.id === "salvage-rift-hulk"), state);
            const routedSalvage = game.salvageSummary(state).sites.find((site) => site.id === "salvage-rift-hulk");

            state.ship.position = { ...state.convoyRoutes[0].beacon.position };
            state = game.deployRouteBeacon(state, "convoy-rift-relay");
            state = game.startConvoyRoute(state, "convoy-rift-relay");
            const stormRoute = game.convoySummary(state).routes[0];
            console.log(JSON.stringify({
              locked,
              deliveredStormCharts: state.contract.deliveredStormCharts,
              baselineRoute,
              stormRoute,
              baselineRisk,
              routedRisk,
              routedSalvage,
              stats: state.stats,
              log: state.log.slice(0, 4).map((entry) => entry.message),
            }));
            """
        )

        self.assertTrue(result["locked"]["storm"]["charted"])
        self.assertTrue(result["locked"]["anchor"]["deployed"])
        self.assertTrue(result["locked"]["safeWindow"]["locked"])
        self.assertEqual(1, result["deliveredStormCharts"])
        self.assertLess(
            result["stormRoute"]["convoy"]["ambushPressure"],
            result["baselineRoute"]["convoy"]["ambushPressure"],
        )
        self.assertLess(
            result["stormRoute"]["convoy"]["hazardExposure"],
            result["baselineRoute"]["convoy"]["hazardExposure"],
        )
        self.assertGreater(
            result["stormRoute"]["convoy"]["payoutCredits"],
            result["baselineRoute"]["convoy"]["payoutCredits"],
        )
        self.assertEqual("locked storm-rift-breaker", result["stormRoute"]["convoy"]["stormWindowStatus"])
        self.assertLess(result["routedRisk"], result["baselineRisk"])
        self.assertEqual("rerouted", result["routedSalvage"]["stormReroute"]["status"])
        self.assertEqual(1, result["stats"]["stormChartsScanned"])
        self.assertEqual(1, result["stats"]["stormAnchorsDeployed"])
        self.assertEqual(1, result["stats"]["stormWindowsLocked"])
        self.assertEqual(1, result["stats"]["stormSalvageReroutes"])
        self.assertTrue(any("safe window locked" in entry for entry in result["log"]))

    def test_station_support_countermeasure_and_resolution_update_ladder_and_payout(self) -> None:
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
            state = game.purchaseStationService(state, "chart-processors");
            state = game.purchaseStationService(state, "storm-plating");
            state = game.purchaseStationService(state, "signal-jammers");
            state = game.setTarget(state, "storm", "storm-rift-breaker");
            state.ship.position = { ...state.stormCharts[0].position };
            state = game.scanStormChart(state, 2);
            const supportedScan = game.stormSummary(state).charts[0];
            state.ship.position = { ...state.stormCharts[0].anchor.position };
            state = game.deployStormAnchor(state, "storm-rift-breaker");
            state.elapsed = 5;
            state.tick = 5;
            state = game.lockStormRouteWindow(state, "storm-rift-breaker");
            state.stormCharts[0].stormState.anchorIntegrity = 42;
            const beforeBurst = game.stormSummary(state).charts[0];
            state = game.stabilizeStormWindow(state, "storm-rift-breaker");
            const afterBurst = game.stormSummary(state).charts[0];
            state = game.resolveStormWindow(state, "storm-rift-breaker");
            const resolved = game.stormSummary(state);
            console.log(JSON.stringify({
              purchased: state.stationServices.purchased,
              supportedScan,
              beforeBurst,
              afterBurst,
              resolved,
              charges: state.stationServices.countermeasureCharges,
              credits: state.credits,
              ladder: state.ladder,
              contract: state.contract,
              stats: state.stats,
            }));
            """
        )

        self.assertEqual(["chart-processors", "storm-plating", "signal-jammers"], result["purchased"])
        self.assertGreater(result["resolved"]["scanPower"], 1)
        self.assertEqual(21, result["supportedScan"]["safeWindow"]["closesAt"])
        self.assertGreater(result["supportedScan"]["anchor"]["maxIntegrity"], 58)
        self.assertTrue(result["afterBurst"]["storm"]["countermeasureUsed"])
        self.assertGreater(result["afterBurst"]["anchor"]["integrity"], result["beforeBurst"]["anchor"]["integrity"])
        self.assertGreater(result["afterBurst"]["safeWindow"]["closesAt"], result["beforeBurst"]["safeWindow"]["closesAt"])
        self.assertEqual(0, result["charges"])
        self.assertEqual("complete", result["resolved"]["charts"][0]["storm"]["outcome"])
        self.assertIn("storm-rift-breaker", result["resolved"]["completedChartIds"])
        self.assertIn("storm-rift-breaker", result["ladder"]["completedStormChartIds"])
        self.assertGreater(result["contract"]["deliveredStormPayout"], 0)
        self.assertGreater(result["credits"], 100)
        self.assertEqual(1, result["stats"]["stormCountermeasures"])

    def test_missed_and_partial_windows_record_distinct_outcomes(self) -> None:
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
            function chartedState() {
              let state = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder });
              state = game.setTarget(state, "storm", "storm-rift-breaker");
              state.ship.position = { ...state.stormCharts[0].position };
              state = game.scanStormChart(state, 2);
              state = game.scanStormChart(state, 2);
              state.ship.position = { ...state.stormCharts[0].anchor.position };
              return game.deployStormAnchor(state, "storm-rift-breaker");
            }

            let missed = chartedState();
            missed.elapsed = 25;
            missed.tick = 25;
            missed = game.resolveStormWindow(missed, "storm-rift-breaker");

            let partial = chartedState();
            partial.elapsed = 5;
            partial.tick = 5;
            partial = game.lockStormRouteWindow(partial, "storm-rift-breaker");
            partial.stormCharts[0].stormState.anchorIntegrity = 28;
            partial = game.resolveStormWindow(partial, "storm-rift-breaker");

            console.log(JSON.stringify({
              missed: game.stormSummary(missed),
              missedHull: missed.ship.hull,
              missedFuel: missed.ship.fuel,
              missedHazard: missed.hazard.exposure,
              missedPirate: missed.pirate.pressure,
              partial: game.stormSummary(partial),
              partialCredits: partial.credits,
              partialContract: partial.contract.deliveredStormPayout,
              partialLadder: partial.ladder,
              partialStats: partial.stats,
            }));
            """
        )

        self.assertEqual("failed", result["missed"]["charts"][0]["storm"]["outcome"])
        self.assertIn("storm-rift-breaker", result["missed"]["failedChartIds"])
        self.assertLess(result["missedHull"], 100)
        self.assertLess(result["missedFuel"], 100)
        self.assertGreater(result["missedHazard"], 0)
        self.assertGreater(result["missedPirate"], 0)
        self.assertEqual("partial", result["partial"]["charts"][0]["storm"]["outcome"])
        self.assertIn("storm-rift-breaker", result["partial"]["partialChartIds"])
        self.assertIn("storm-rift-breaker", result["partial"]["completedChartIds"])
        self.assertGreater(result["partialCredits"], 0)
        self.assertEqual(result["partialCredits"], result["partialContract"])
        self.assertIn("storm-rift-breaker", result["partialLadder"]["completedStormChartIds"])
        self.assertGreater(result["partialLadder"]["stormScore"], 0)
        self.assertEqual(1, result["partialStats"]["stormPartialPayouts"])

    def test_tempest_verge_late_run_contract_and_reset_carry_storm_state(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/void-prospector/void-prospector.js");
            const ladder = {
              currentSectorId: "tempest-verge",
              recommendedSectorId: "tempest-verge",
              unlockedSectorIds: ["spoke-approach", "rift-shelf", "umbra-trench", "tempest-verge"],
              completedSectorIds: ["spoke-approach", "rift-shelf", "umbra-trench"],
            };
            let state = game.createInitialState({ seed: 77, sectorId: "tempest-verge", ladder });
            const eye = state.anomalies.find((node) => node.id === "anomaly-tempest-eye");
            state.ship.position = { ...eye.position };
            state = game.setTarget(state, "anomaly", eye.id);
            state = game.scanTarget(state, 2);
            state = game.scanTarget(state, 2);
            state = game.setTarget(state, "storm", "storm-tempest-verge");
            state.ship.position = { ...state.stormCharts[0].position };
            state = game.scanStormChart(state, 2);
            state = game.scanStormChart(state, 2);
            state = game.scanStormChart(state, 1);
            state.ship.position = { ...state.stormCharts[0].anchor.position };
            state = game.deployStormAnchor(state, "storm-tempest-verge");
            state.elapsed = 9;
            state.tick = 9;
            state = game.lockStormRouteWindow(state, "storm-tempest-verge");
            const routeReady = game.convoyRouteReadiness(state, "convoy-tempest-relay");
            state = game.resolveStormWindow(state, "storm-tempest-verge");
            const afterStorm = JSON.parse(JSON.stringify(state));
            state.ship.position = { ...state.station.position };
            state.cargo.ore = 14;
            state.cargo.value = 700;
            state = game.dockAtStation(state);
            const reset = game.resetRun(state);
            console.log(JSON.stringify({
              sectorCount: game.GAME_DATA.surveyLadder.sectors.length,
              tempestContract: afterStorm.contract,
              routeReady,
              finalStatus: state.contract.status,
              runStatus: state.run.status,
              completedSectors: state.ladder.completedSectorIds,
              unlockedSectors: state.ladder.unlockedSectorIds,
              stormScore: state.ladder.stormScore,
              resetStormCharts: reset.ladder.completedStormChartIds,
              resetStormSummary: game.stormSummary(reset),
            }));
            """
        )

        self.assertGreaterEqual(result["sectorCount"], 4)
        self.assertEqual(1, result["tempestContract"]["deliveredStormCharts"])
        self.assertGreaterEqual(result["tempestContract"]["deliveredStormPayout"], 200)
        self.assertTrue(result["routeReady"]["ready"])
        self.assertEqual("complete", result["finalStatus"])
        self.assertEqual("complete", result["runStatus"])
        self.assertIn("tempest-verge", result["completedSectors"])
        self.assertIn("tempest-verge", result["unlockedSectors"])
        self.assertGreater(result["stormScore"], 0)
        self.assertIn("storm-tempest-verge", result["resetStormCharts"])
        self.assertEqual("0.4.0", result["resetStormSummary"]["version"])

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
