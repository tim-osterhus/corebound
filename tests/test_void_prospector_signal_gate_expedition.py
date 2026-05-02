import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VoidProspectorSignalGateExpeditionTests(unittest.TestCase):
    def test_signal_gate_generation_adds_v060_state_without_replacing_knife_wake(self) -> None:
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
                scannedAnomalyIds: ["anomaly-black-pylon"],
                salvageManifestIds: ["salvage-umbra-blackbox"],
                hazardCharts: { "umbra-trench": true },
              },
            });
            const target = game.setTarget(rift, "signal-gate", "gate-rift-relay-aperture");
            console.log(JSON.stringify({
              interdictionVersion: rift.interdiction.version,
              signalVersion: rift.signalGate.version,
              signalLabel: rift.signalGate.releaseLabel,
              riftGate: game.signalGateSummary(rift).gates[0],
              umbraGate: game.signalGateSummary(umbra).gates[0],
              target: game.targetSummary(target),
              generatedCount:
                game.createSignalGates(44, game.sectorById("rift-shelf")).length +
                game.createSignalGates(52, game.sectorById("umbra-trench")).length +
                game.createSignalGates(77, game.sectorById("tempest-verge")).length,
            }));
            """
        )

        self.assertEqual("0.5.0", result["interdictionVersion"])
        self.assertEqual("0.6.0", result["signalVersion"])
        self.assertEqual("Signal Gate Expedition", result["signalLabel"])
        self.assertGreaterEqual(result["generatedCount"], 2)
        self.assertEqual("gate-rift-relay-aperture", result["riftGate"]["id"])
        self.assertEqual("convoy-rift-relay", result["riftGate"]["routeAssociation"])
        self.assertIn("deploy convoy-rift-relay beacon", result["riftGate"]["missingPrerequisites"])
        self.assertEqual("pylon-rift-relay", result["riftGate"]["pylon"]["id"])
        self.assertIn("position", result["riftGate"]["lattice"])
        self.assertGreater(result["riftGate"]["capacitorRequirement"], 0)
        self.assertGreater(result["riftGate"]["transitWindow"]["closesAt"], result["riftGate"]["transitWindow"]["opensAt"])
        self.assertEqual("gate-umbra-blackbox-lattice", result["umbraGate"]["id"])
        self.assertIn("lock storm-umbra-knife-wake", result["umbraGate"]["missingPrerequisites"])
        self.assertIn("salvage-umbra-blackbox", result["umbraGate"]["targets"]["salvageSiteIds"])
        self.assertEqual("signal-gate", result["target"]["kind"])
        self.assertEqual("convoy-lane", result["target"]["family"])
        self.assertIn("harmonics", result["target"]["status"])

    def test_scan_align_charge_and_convoy_transit_couple_route_salvage_payout_and_log(self) -> None:
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
            let baseline = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder });
            baseline.ship.position = { ...baseline.convoyRoutes[0].beacon.position };
            baseline = game.deployRouteBeacon(baseline, "convoy-rift-relay");
            const baselineRisk = game.salvageRisk(
              baseline.salvageSites.find((site) => site.id === "salvage-rift-hulk"),
              baseline
            );

            let state = game.createInitialState({
              seed: 44,
              sectorId: "rift-shelf",
              ladder,
              stationServices: { purchased: ["gate-tuners"] },
            });
            state.ship.position = { ...state.convoyRoutes[0].beacon.position };
            state = game.deployRouteBeacon(state, "convoy-rift-relay");
            state = game.setTarget(state, "signal-gate", "gate-rift-relay-aperture");
            state.ship.position = { ...state.signalGates[0].position };
            state = game.scanSignalGateHarmonics(state, "gate-rift-relay-aperture", 2);
            state = game.scanSignalGateHarmonics(state, "gate-rift-relay-aperture", 1);
            state.ship.position = { ...state.signalGates[0].pylon.position };
            state = game.alignSignalGatePylon(state, "gate-rift-relay-aperture");
            state.ship.position = { ...state.signalGates[0].position };
            state = game.chargeSignalGateCapacitor(state, "gate-rift-relay-aperture", 2);
            state = game.chargeSignalGateCapacitor(state, "gate-rift-relay-aperture", 2);
            state.elapsed = 6;
            state.tick = 6;
            state = game.commitSignalGateTransit(state, "gate-rift-relay-aperture", "convoy");
            const resolvedRisk = game.salvageRisk(
              state.salvageSites.find((site) => site.id === "salvage-rift-hulk"),
              state
            );
            console.log(JSON.stringify({
              signal: game.signalGateSummary(state),
              convoy: game.convoySummary(state),
              baselineRisk,
              resolvedRisk,
              salvage: game.salvageSummary(state).sites.find((site) => site.id === "salvage-rift-hulk"),
              target: game.targetSummary(state),
              contract: state.contract,
              credits: state.credits,
              fuel: state.ship.fuel,
              stats: state.stats,
              log: state.log.slice(0, 6).map((entry) => entry.message),
            }));
            """
        )

        gate = result["signal"]["gates"][0]
        route = result["convoy"]["routes"][0]
        self.assertEqual("success", gate["state"]["outcome"])
        self.assertIn("gate-rift-relay-aperture", result["signal"]["completedGateIds"])
        self.assertIn("gate-rift-relay-aperture", result["signal"]["scannedGateIds"])
        self.assertIn("gate-rift-relay-aperture", result["signal"]["alignedGateIds"])
        self.assertIn("gate-rift-relay-aperture", result["signal"]["chargedGateIds"])
        self.assertEqual("delivered", route["convoy"]["status"])
        self.assertEqual("gate-rift-relay-aperture success", route["convoy"]["signalGateStatus"])
        self.assertGreater(result["convoy"]["payoutBanked"], 0)
        self.assertLess(result["resolvedRisk"], result["baselineRisk"])
        self.assertEqual("transit shielded", result["salvage"]["signalGateShield"]["status"])
        self.assertEqual(1, result["contract"]["deliveredSignalTransits"])
        self.assertGreater(result["contract"]["deliveredSignalPayout"], 0)
        self.assertGreater(result["credits"], result["contract"]["deliveredSignalPayout"])
        self.assertLess(result["fuel"], 100)
        self.assertEqual(1, result["stats"]["signalGateScans"])
        self.assertEqual(1, result["stats"]["signalPylonsAligned"])
        self.assertEqual(1, result["stats"]["signalCapacitorsCharged"])
        self.assertEqual(1, result["stats"]["signalGateTransits"])
        self.assertEqual(1, result["stats"]["signalGateConvoyTransits"])
        self.assertTrue(any("Signal Gate" in entry or "Signal Gate Expedition" in entry for entry in result["log"]))

    def test_blackbox_gate_requires_storm_window_and_station_tuning_mitigates_gate_jam(self) -> None:
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
            const locked = game.createInitialState({ seed: 52, sectorId: "umbra-trench", ladder });

            let state = game.createInitialState({ seed: 52, sectorId: "umbra-trench", ladder, credits: 500 });
            state.ship.position = { ...state.station.position };
            state = game.purchaseStationService(state, "gate-tuners");
            state = game.setTarget(state, "storm", "storm-umbra-knife-wake");
            state.ship.position = { ...state.stormCharts[0].position };
            state = game.scanStormChart(state, 2);
            state = game.scanStormChart(state, 2);
            state.ship.position = { ...state.stormCharts[0].anchor.position };
            state = game.deployStormAnchor(state, "storm-umbra-knife-wake");
            state.elapsed = 7;
            state.tick = 7;
            state = game.lockStormRouteWindow(state, "storm-umbra-knife-wake");
            state = game.setTarget(state, "signal-gate", "gate-umbra-blackbox-lattice");
            state.ship.position = { ...state.signalGates[0].position };
            state = game.scanSignalGateHarmonics(state, "gate-umbra-blackbox-lattice", 2);
            state = game.scanSignalGateHarmonics(state, "gate-umbra-blackbox-lattice", 1);
            const beforeJam = game.signalGateSummary(state).gates[0];
            state = game.mitigateSignalGateJam(state, "gate-umbra-blackbox-lattice");
            state.ship.position = { ...state.signalGates[0].pylon.position };
            state = game.alignSignalGatePylon(state, "gate-umbra-blackbox-lattice");
            const beforeAnchor = game.signalGateSummary(state).gates[0];
            state = game.anchorSignalGateStormWindow(state, "gate-umbra-blackbox-lattice", "storm-umbra-knife-wake");
            const anchored = game.signalGateSummary(state).gates[0];
            console.log(JSON.stringify({
              lockedGate: game.signalGateSummary(locked).gates[0],
              purchased: state.stationServices.purchased,
              support: game.signalGateSummary(state),
              beforeJam,
              afterJam: game.signalGateSummary(state).gates[0],
              beforeAnchor,
              anchored,
              charges: state.stationServices.countermeasureCharges,
              stats: state.stats,
              log: state.log.slice(0, 6).map((entry) => entry.message),
            }));
            """
        )

        self.assertIn("lock storm-umbra-knife-wake", result["lockedGate"]["missingPrerequisites"])
        self.assertEqual(["gate-tuners"], result["purchased"])
        self.assertGreater(result["support"]["scanPower"], 1)
        self.assertGreater(result["support"]["pylonSupportIntegrity"], 0)
        self.assertGreater(result["beforeJam"]["pirateJam"], result["afterJam"]["pirateJam"])
        self.assertGreater(result["afterJam"]["capacitorCharge"], 0)
        self.assertEqual(0, result["charges"])
        self.assertEqual(1, result["stats"]["signalGateJamsMitigated"])
        self.assertIsNone(result["beforeAnchor"]["transitWindow"]["anchoredChartId"])
        self.assertEqual("storm-umbra-knife-wake", result["anchored"]["transitWindow"]["anchoredChartId"])
        self.assertGreater(result["anchored"]["transitWindow"]["closesAt"], result["beforeAnchor"]["transitWindow"]["closesAt"])
        self.assertTrue(any("pirate gate interference" in entry or "anchored" in entry for entry in result["log"]))

    def test_partial_failure_and_reset_carryover_are_recorded_separately(self) -> None:
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
            function chargedState() {
              let state = game.createInitialState({ seed: 44, sectorId: "rift-shelf", ladder });
              state.ship.position = { ...state.convoyRoutes[0].beacon.position };
              state = game.deployRouteBeacon(state, "convoy-rift-relay");
              state.ship.position = { ...state.signalGates[0].position };
              state = game.scanSignalGateHarmonics(state, "gate-rift-relay-aperture", 2);
              state = game.scanSignalGateHarmonics(state, "gate-rift-relay-aperture", 1);
              state.ship.position = { ...state.signalGates[0].pylon.position };
              state = game.alignSignalGatePylon(state, "gate-rift-relay-aperture");
              state.ship.position = { ...state.signalGates[0].position };
              state = game.chargeSignalGateCapacitor(state, "gate-rift-relay-aperture", 2);
              state = game.chargeSignalGateCapacitor(state, "gate-rift-relay-aperture", 2);
              state.elapsed = 6;
              state.tick = 6;
              return state;
            }

            let partial = chargedState();
            partial.signalGates[0].gateState.pirateJam = 100;
            partial = game.commitSignalGateTransit(partial, "gate-rift-relay-aperture", "solo");
            const reset = game.resetRun(partial);

            let failed = chargedState();
            failed.signalGates[0].gateState.pirateJam = 180;
            failed.cargo.ore = 2;
            failed.cargo.value = 100;
            failed = game.commitSignalGateTransit(failed, "gate-rift-relay-aperture", "solo");
            console.log(JSON.stringify({
              partial: game.signalGateSummary(partial),
              partialHull: partial.ship.hull,
              partialFuel: partial.ship.fuel,
              reset: game.signalGateSummary(reset),
              resetLadder: reset.ladder,
              failed: game.signalGateSummary(failed),
              failedHull: failed.ship.hull,
              failedFuel: failed.ship.fuel,
              failedCargo: failed.cargo,
              failedStats: failed.stats,
            }));
            """
        )

        self.assertEqual("partial", result["partial"]["gates"][0]["state"]["outcome"])
        self.assertIn("gate-rift-relay-aperture", result["partial"]["partialGateIds"])
        self.assertGreater(result["partial"]["payoutBanked"], 0)
        self.assertLess(result["partialHull"], 100)
        self.assertLess(result["partialFuel"], 100)
        self.assertIn("gate-rift-relay-aperture", result["resetLadder"]["completedSignalGateIds"])
        self.assertEqual("0.6.0", result["reset"]["version"])
        self.assertEqual("failed", result["failed"]["gates"][0]["state"]["outcome"])
        self.assertIn("gate-rift-relay-aperture", result["failed"]["failedGateIds"])
        self.assertLess(result["failedHull"], 100)
        self.assertLess(result["failedFuel"], 100)
        self.assertLess(result["failedCargo"]["ore"], 2)
        self.assertEqual(1, result["failedStats"]["signalGateFailures"])

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
