import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class IronLanternDescentEchoRelayNetworkTests(unittest.TestCase):
    def test_echo_relay_data_extends_progression_and_scanner_targeting(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/iron-lantern-descent/iron-lantern-descent.js");
            let state = game.createInitialState({ seed: 501 });
            const relay = state.relaySites.find((site) => site.id === "relay-cinder-echo-pylon");
            state.player.position = { x: relay.position.x, y: 1.6, z: relay.position.z };
            state.elapsed = 90;
            state = game.pulseScanner(game.syncDerivedState(state));
            const nearest = game.nearestRelaySite(state);

            console.log(JSON.stringify({
              release: state.echoRelayNetwork.release.label,
              baseRelease: state.echoRelayNetwork.release.baseRelease,
              ventRelease: state.ventNetwork.release.label,
              passageIds: game.GAME_DATA.cave.passages.map((passage) => passage.id),
              collisionPassage: state.movement.collision.lastPassage,
              relayCount: state.relaySites.length,
              nearestRelay: nearest.site.id,
              activeRelay: state.echoRelayNetwork.activeSiteId,
              scannerKind: state.scanner.targetKind,
              scannerPulseKind: state.scanner.lastPulse.targetKind,
              scannerPulseWindow: state.scanner.lastPulse.echoRelayWindow,
              scannerPulseStatus: state.scanner.lastPulse.echoRelayStatus,
              relayId: relay.relayId,
              cableSpanId: relay.cableSpanId,
              cableState: relay.cableState,
              echoCharge: relay.echoCharge,
              cacheState: relay.cacheState.status,
              beaconState: relay.beaconState,
              requirement: relay.requirements,
              contractTriangulations: state.echoRelayNetwork.contract.targetTriangulations,
              contractCaches: state.echoRelayNetwork.contract.targetCaches,
              contractBeacons: state.echoRelayNetwork.contract.targetBeacons,
              contractMap: state.echoRelayNetwork.contract.targetMapProgress,
              echoCharges: state.echoRelayNetwork.echoCharges,
            }));
            """
        )

        self.assertEqual("v0.4.0 Echo Relay Network", result["release"])
        self.assertEqual("v0.3.0 Cinder Vent Network", result["baseRelease"])
        self.assertEqual("v0.3.0 Cinder Vent Network", result["ventRelease"])
        self.assertIn("echo-relay-alcove", result["passageIds"])
        self.assertIn("lift-beacon-station", result["passageIds"])
        self.assertEqual("echo-relay-alcove", result["collisionPassage"])
        self.assertGreaterEqual(result["relayCount"], 2)
        self.assertEqual("relay-cinder-echo-pylon", result["nearestRelay"])
        self.assertEqual("relay-cinder-echo-pylon", result["activeRelay"])
        self.assertEqual("echo-relay", result["scannerKind"])
        self.assertEqual("echo-relay", result["scannerPulseKind"])
        self.assertEqual("clear", result["scannerPulseWindow"])
        self.assertEqual("relay ready", result["scannerPulseStatus"])
        self.assertEqual("echo-cinder-pylon", result["relayId"])
        self.assertEqual("cable-cinder-lantern-line", result["cableSpanId"])
        self.assertEqual("broken", result["cableState"])
        self.assertEqual(1, result["echoCharge"])
        self.assertEqual("sealed", result["cacheState"])
        self.assertEqual("armed", result["beaconState"])
        self.assertEqual("survey-cinder-rib", result["requirement"]["surveySiteId"])
        self.assertEqual("pump-cinder-sump", result["requirement"]["pumpworksSiteId"])
        self.assertEqual("vent-cinder-rib-draft", result["requirement"]["ventSiteId"])
        self.assertEqual("partial", result["requirement"]["ventRelay"])
        self.assertEqual(2, result["contractTriangulations"])
        self.assertEqual(2, result["contractCaches"])
        self.assertEqual(1, result["contractBeacons"])
        self.assertEqual(3, result["contractMap"])
        self.assertEqual(2, result["echoCharges"])

    def test_cinder_relay_repair_cable_triangulation_cache_and_beacon_are_stateful(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/iron-lantern-descent/iron-lantern-descent.js");
            let state = game.createInitialState({ seed: 503 });

            const survey = state.surveySites.find((site) => site.id === "survey-cinder-rib");
            state.player.position = { x: survey.position.x, y: 1.6, z: survey.position.z };
            state = game.placeLantern(game.syncDerivedState(state));
            state = game.plantSurveyStake(state, "survey-cinder-rib");
            state = game.chartFaultSurvey(state, "survey-cinder-rib");

            const pump = state.pumpworksSites.find((site) => site.id === "pump-cinder-sump");
            state.player.position = { x: pump.position.x, y: 1.6, z: pump.position.z };
            state.elapsed = 72;
            state = game.placeLantern(game.syncDerivedState(state));
            state = game.primePumpStation(state, "pump-cinder-sump");
            state = game.turnPressureValve(state, "pump-cinder-sump");

            const vent = state.ventSites.find((site) => site.id === "vent-cinder-rib-draft");
            state.player.position = { x: vent.position.x, y: 1.6, z: vent.position.z };
            state.elapsed = 90;
            state = game.openDraftGate(game.syncDerivedState(state), "vent-cinder-rib-draft");
            state = game.startPressureFan(state, "vent-cinder-rib-draft");
            state = game.ventGasPocket(state, "vent-cinder-rib-draft");

            const relay = state.relaySites.find((site) => site.id === "relay-cinder-echo-pylon");
            state.player.position = { x: relay.position.x, y: 1.6, z: relay.position.z };
            state.elapsed = 118;
            state = game.pulseScanner(game.syncDerivedState(state));
            const before = {
              targetKind: state.scanner.targetKind,
              pulseKind: state.scanner.lastPulse.targetKind,
              route: state.route.returnConfidence,
              stability: state.routeStability.stability,
              drain: game.oxygenDrainRate(state),
              oxygen: state.oxygen.current,
              charges: state.echoRelayNetwork.echoCharges,
            };
            state = game.repairRelayPylon(state, "relay-cinder-echo-pylon");
            const repaired = JSON.parse(JSON.stringify(state));
            state = game.spoolRelayCable(state, "relay-cinder-echo-pylon");
            const spooled = JSON.parse(JSON.stringify(state));
            state = game.triangulateEchoRoute(state, "relay-cinder-echo-pylon");
            const triangulated = JSON.parse(JSON.stringify(state));
            const oxygenBeforeCache = state.oxygen.current;
            state = game.claimRescueCache(state, "relay-cinder-echo-pylon");
            const cached = JSON.parse(JSON.stringify(state));
            state.cargo.value = 40;
            state = game.fireLiftBeacon(state, "relay-cinder-echo-pylon");
            const beaconed = JSON.parse(JSON.stringify(state));
            const deepLode = state.sampleNodes.find((node) => node.id === "sample-deep-lode");

            console.log(JSON.stringify({
              before,
              pylonState: repaired.relaySites[0].pylonState,
              repairNoise: repaired.relaySites[0].echoNoise,
              cableState: spooled.relaySites[0].cableState,
              cablePressure: spooled.relaySites[0].cableBreakPressure,
              pulseState: spooled.relaySites[0].pulseState,
              triangulationState: triangulated.relaySites[0].triangulationState,
              relayValue: triangulated.echoRelayNetwork.value,
              relayMap: triangulated.echoRelayNetwork.mapProgress,
              routeRelief: triangulated.echoRelayNetwork.routeRelief,
              chargesAfter: triangulated.echoRelayNetwork.echoCharges,
              routeAfter: triangulated.route.returnConfidence,
              stabilityAfter: triangulated.routeStability.stability,
              drainAfter: game.oxygenDrainRate(triangulated),
              cacheState: cached.relaySites[0].cacheState.status,
              oxygenBeforeCache,
              oxygenAfterCache: cached.oxygen.current,
              cargoAfterCache: cached.cargo.value,
              cachesClaimed: cached.echoRelayNetwork.cachesClaimed,
              beaconState: beaconed.relaySites[0].beaconState,
              cargoAfterBeacon: beaconed.cargo.value,
              beaconsFired: beaconed.echoRelayNetwork.beaconsFired,
              sampleRelayBonus: game.sampleRelayValueBonus(beaconed, deepLode),
              routeGuideKinds: game.routeGuidePoints(triangulated).map((point) => point.kind),
              triangulationLog: triangulated.log[0].message,
              beaconLog: beaconed.log[0].message,
            }));
            """
        )

        self.assertEqual("echo-relay", result["before"]["targetKind"])
        self.assertEqual("echo-relay", result["before"]["pulseKind"])
        self.assertEqual("repaired", result["pylonState"])
        self.assertLess(result["repairNoise"], 0.42)
        self.assertEqual("spooled", result["cableState"])
        self.assertLess(result["cablePressure"], 0.2)
        self.assertEqual("charged", result["pulseState"])
        self.assertEqual("success", result["triangulationState"])
        self.assertEqual(88, result["relayValue"])
        self.assertEqual(1, result["relayMap"])
        self.assertEqual(18, result["routeRelief"])
        self.assertEqual(result["before"]["charges"] - 1, result["chargesAfter"])
        self.assertGreater(result["routeAfter"], result["before"]["route"])
        self.assertGreater(result["stabilityAfter"], result["before"]["stability"])
        self.assertLess(result["drainAfter"], result["before"]["drain"])
        self.assertEqual("claimed", result["cacheState"])
        self.assertGreater(result["oxygenAfterCache"], result["oxygenBeforeCache"])
        self.assertEqual(16, result["cargoAfterCache"])
        self.assertEqual(1, result["cachesClaimed"])
        self.assertEqual("fired", result["beaconState"])
        self.assertEqual(30, result["cargoAfterBeacon"])
        self.assertEqual(1, result["beaconsFired"])
        self.assertEqual(11, result["sampleRelayBonus"])
        self.assertIn("echo-relay", result["routeGuideKinds"])
        self.assertIn("echo triangulation success", result["triangulationLog"])
        self.assertIn("emergency lift beacon fired", result["beaconLog"])

    def test_basalt_beacon_banking_restart_carryover_and_sample_bonus(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/iron-lantern-descent/iron-lantern-descent.js");
            let state = game.createInitialState({ seed: 509, purchasedUpgrades: ["lantern-frame"] });

            const survey = state.surveySites.find((site) => site.id === "survey-basalt-suture");
            state.player.position = { x: survey.position.x, y: 1.6, z: survey.position.z };
            state.elapsed = 50;
            state = game.placeLantern(game.syncDerivedState(state));
            state = game.plantSurveyStake(state, "survey-basalt-suture");
            state = game.braceSurveySite(state, "survey-basalt-suture");
            state = game.chartFaultSurvey(state, "survey-basalt-suture");

            const pump = state.pumpworksSites.find((site) => site.id === "pump-basalt-gate");
            state.player.position = { x: pump.position.x, y: 1.6, z: pump.position.z };
            state.elapsed = 90;
            state = game.placeLantern(game.syncDerivedState(state));
            state = game.sealLeakSeam(state, "pump-basalt-gate");
            state = game.deploySiphonCharge(state, "pump-basalt-gate");
            state = game.primePumpStation(state, "pump-basalt-gate");
            state = game.turnPressureValve(state, "pump-basalt-gate");

            const vent = state.ventSites.find((site) => site.id === "vent-basalt-relay-bay");
            state.player.position = { x: vent.position.x, y: 1.6, z: vent.position.z };
            state.elapsed = 110;
            state = game.placeLantern(game.syncDerivedState(state));
            state = game.openDraftGate(state, "vent-basalt-relay-bay");
            state = game.deployFilterCartridge(state, "vent-basalt-relay-bay");
            state = game.startPressureFan(state, "vent-basalt-relay-bay");
            state = game.ventGasPocket(state, "vent-basalt-relay-bay");

            const relay = state.relaySites.find((site) => site.id === "relay-basalt-beacon-station");
            state.player.position = { x: relay.position.x, y: 1.6, z: relay.position.z };
            state.elapsed = 130;
            state = game.placeLantern(game.syncDerivedState(state));
            const beforeRelay = {
              route: state.route.returnConfidence,
              stability: state.routeStability.stability,
              drain: game.oxygenDrainRate(state),
            };
            state = game.repairRelayPylon(state, "relay-basalt-beacon-station");
            state = game.spoolRelayCable(state, "relay-basalt-beacon-station");
            const spooled = JSON.parse(JSON.stringify(state));
            state = game.triangulateEchoRoute(state, "relay-basalt-beacon-station");
            const triangulated = JSON.parse(JSON.stringify(state));
            state.oxygen.current = 40;
            state = game.claimRescueCache(state, "relay-basalt-beacon-station");
            const cached = JSON.parse(JSON.stringify(state));
            state.cargo.value = 60;
            state = game.fireLiftBeacon(state, "relay-basalt-beacon-station");
            const beaconed = JSON.parse(JSON.stringify(state));

            const quartz = state.sampleNodes.find((node) => node.id === "sample-echo-quartz");
            state.player.position = { x: quartz.position.x, y: 1.6, z: quartz.position.z };
            state = game.syncDerivedState(state);
            for (let pass = 0; pass < 3; pass += 1) {
              state = game.mineNearestSample(state, 1);
            }
            const mined = JSON.parse(JSON.stringify(state));
            state.player.position = { x: state.lift.position.x, y: 1.6, z: state.lift.position.z };
            state = game.returnToLift(game.syncDerivedState(state));
            const afterLift = JSON.parse(JSON.stringify(state));
            const restarted = game.resetRun(state);

            console.log(JSON.stringify({
              beforeRelay,
              cableState: spooled.relaySites[1].cableState,
              triangulationState: triangulated.relaySites[1].triangulationState,
              relayValue: triangulated.echoRelayNetwork.value,
              relayMap: triangulated.echoRelayNetwork.mapProgress,
              routeRelief: triangulated.echoRelayNetwork.routeRelief,
              routeAfter: triangulated.route.returnConfidence,
              stabilityAfter: triangulated.routeStability.stability,
              drainAfter: game.oxygenDrainRate(triangulated),
              cacheState: cached.relaySites[1].cacheState.status,
              oxygenAfterCache: cached.oxygen.current,
              cargoAfterCache: cached.cargo.value,
              beaconState: beaconed.relaySites[1].beaconState,
              cargoAfterBeacon: beaconed.cargo.value,
              beaconsFired: beaconed.echoRelayNetwork.beaconsFired,
              sampleRelayBonus: game.sampleRelayValueBonus(beaconed, quartz),
              minedValue: mined.cargo.value,
              lastYield: mined.sampleNodes.find((node) => node.id === "sample-echo-quartz").mineState.lastYield,
              bankedCredits: afterLift.credits,
              bankedSurveyValue: afterLift.lift.bankedSurveyValue,
              bankedPumpworksValue: afterLift.lift.bankedPumpworksValue,
              bankedVentValue: afterLift.lift.bankedVentValue,
              bankedEchoRelayValue: afterLift.lift.bankedEchoRelayValue,
              bankedEchoRelayMapProgress: afterLift.lift.bankedEchoRelayMapProgress,
              echoLedger: afterLift.echoRelayNetwork.ledger,
              echoValueAfterLift: afterLift.echoRelayNetwork.value,
              restartedEchoLedger: restarted.echoRelayNetwork.ledger,
              restartedEchoCharges: restarted.echoRelayNetwork.echoCharges,
              upgradedEchoCharges: game.createInitialState({ purchasedUpgrades: ["echo-capacitor"] }).echoRelayNetwork.echoCharges,
              restartedRunCount: restarted.run.count,
            }));
            """
        )

        self.assertEqual("spooled", result["cableState"])
        self.assertEqual("success", result["triangulationState"])
        self.assertEqual(132, result["relayValue"])
        self.assertEqual(2, result["relayMap"])
        self.assertEqual(24, result["routeRelief"])
        self.assertGreater(result["routeAfter"], result["beforeRelay"]["route"])
        self.assertGreater(result["stabilityAfter"], result["beforeRelay"]["stability"])
        self.assertLess(result["drainAfter"], result["beforeRelay"]["drain"])
        self.assertEqual("claimed", result["cacheState"])
        self.assertEqual(58, result["oxygenAfterCache"])
        self.assertEqual(24, result["cargoAfterCache"])
        self.assertEqual("fired", result["beaconState"])
        self.assertEqual(40, result["cargoAfterBeacon"])
        self.assertEqual(1, result["beaconsFired"])
        self.assertEqual(17, result["sampleRelayBonus"])
        self.assertEqual(131, result["minedValue"])
        self.assertEqual(91, result["lastYield"])
        self.assertEqual(545, result["bankedCredits"])
        self.assertEqual(78, result["bankedSurveyValue"])
        self.assertEqual(96, result["bankedPumpworksValue"])
        self.assertEqual(108, result["bankedVentValue"])
        self.assertEqual(132, result["bankedEchoRelayValue"])
        self.assertEqual(2, result["bankedEchoRelayMapProgress"])
        self.assertEqual(2, result["echoLedger"])
        self.assertEqual(0, result["echoValueAfterLift"])
        self.assertEqual(2, result["restartedEchoLedger"])
        self.assertEqual(2, result["restartedEchoCharges"])
        self.assertEqual(3, result["upgradedEchoCharges"])
        self.assertEqual(2, result["restartedRunCount"])

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
