import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DarkFactoryDispatchFirstShiftTests(unittest.TestCase):
    def test_initial_state_exposes_guided_tutorial_selection_and_disclosure(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/dark-factory-dispatch/dark-factory-dispatch.js");
            const state = game.createInitialState({ seed: 701 });

            console.log(JSON.stringify({
              tutorialStatus: state.tutorial.status,
              tutorialStep: state.tutorial.stepId,
              trainingContract: state.tutorial.contract.id,
              selectedJobId: state.selection.selectedJobId,
              selectedLaneId: state.selection.selectedLaneId,
              beginnerVisible: state.disclosure.beginnerVisible,
              visibleResources: state.disclosure.visibleResources,
              gridVisible: state.disclosure.systems.gridSiege.visible,
              breachVisible: state.disclosure.systems.signalBreach.visible,
              freightVisible: state.disclosure.systems.freightLockdown.visible,
              railVisible: state.disclosure.systems.railSabotage.visible,
              crisisVisible: state.disclosure.systems.crisisArbitration.visible,
              preservedGridRelease: state.grid.release,
              preservedBreachRelease: state.breach.release,
              preservedFreightRelease: state.freight.release,
              preservedRailRelease: state.railSabotage.release,
              preservedCrisisRelease: state.crisisArbitration.release,
            }));
            """
        )

        self.assertEqual("active", result["tutorialStatus"])
        self.assertEqual("select-smelt-circuits", result["tutorialStep"])
        self.assertEqual("training-circuits", result["trainingContract"])
        self.assertIsNone(result["selectedJobId"])
        self.assertIsNone(result["selectedLaneId"])
        self.assertTrue(result["beginnerVisible"])
        self.assertEqual(["scrap", "power", "stability"], result["visibleResources"])
        self.assertFalse(result["gridVisible"])
        self.assertFalse(result["breachVisible"])
        self.assertFalse(result["freightVisible"])
        self.assertFalse(result["railVisible"])
        self.assertFalse(result["crisisVisible"])
        self.assertEqual("v0.4.0 Freight Lockdown", result["preservedGridRelease"])
        self.assertEqual("v0.4.0 Freight Lockdown", result["preservedBreachRelease"])
        self.assertEqual("v0.4.0 Freight Lockdown", result["preservedFreightRelease"])
        self.assertEqual("v0.5.0 Rail Sabotage", result["preservedRailRelease"])
        self.assertEqual("v0.6.0 Crisis Arbitration", result["preservedCrisisRelease"])

    def test_click_first_training_shift_reaches_recovery_contract_and_summary(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/dark-factory-dispatch/dark-factory-dispatch.js");
            let state = game.createInitialState({ seed: 1972, faultGraceTicks: 0 });
            const smeltEntry = state.queue.find((entry) => entry.jobTypeId === "smelt-circuits");

            state = game.selectJobCard(state, smeltEntry.id);
            const afterJobSelect = {
              step: state.tutorial.stepId,
              selectedJobId: state.selection.selectedJobId,
            };

            state = game.selectLane(state, "forge-line");
            const assignAction = state.contextualActions.find((action) => action.id === "assign");
            state = game.performContextAction(state, "assign");
            const assigned = state.lanes.find((lane) => lane.id === "forge-line");

            const startAction = state.contextualActions.find((action) => action.id === "start");
            state = game.performContextAction(state, "start");
            state = game.stepFactory(state, 1);
            const jammed = state.lanes.find((lane) => lane.id === "forge-line");

            const recoverAction = state.contextualActions.find((action) => action.id === "recover");
            state = game.performContextAction(state, "recover");
            const recovering = state.lanes.find((lane) => lane.id === "forge-line");
            state = game.stepFactory(state, recovering.recoveryRemaining);
            const recovered = state.lanes.find((lane) => lane.id === "forge-line");
            const recoveredStep = state.tutorial.stepId;

            state = game.performContextAction(state, "start");
            state = game.stepFactory(state, recovered.currentJob.remaining);
            const finalLane = state.lanes.find((lane) => lane.id === "forge-line");

            console.log(JSON.stringify({
              afterJobSelect,
              assignAvailable: assignAction && assignAction.available,
              assignedStatus: assigned.status,
              assignedJob: assigned.currentJob.jobTypeId,
              startAvailable: startAction && startAction.available,
              jamStep: state.tutorial.events.some((event) => event.stepId === "recover-material-jam"),
              jamStatus: jammed.status,
              jamFault: jammed.fault && jammed.fault.id,
              recoverAvailable: recoverAction && recoverAction.available,
              recoveringStatus: recovering.status,
              recoveredStatus: recovered.status,
              recoveredStep,
              finalLaneStatus: finalLane.status,
              producedCircuits: state.produced.circuits,
              tutorialStatus: state.tutorial.status,
              tutorialCompleted: state.tutorial.completed,
              tutorialContractStatus: state.tutorial.contract.status,
              shiftStatus: state.shift.status,
              summaryOpen: Boolean(state.shift.summary),
              upgradeChoiceStatus: state.shift.upgradeChoice.status,
              contextualActionIds: state.contextualActions.map((action) => action.id),
            }));
            """
        )

        self.assertEqual("select-forge-line", result["afterJobSelect"]["step"])
        self.assertTrue(result["afterJobSelect"]["selectedJobId"].startswith("q"))
        self.assertTrue(result["assignAvailable"])
        self.assertEqual("assigned", result["assignedStatus"])
        self.assertEqual("smelt-circuits", result["assignedJob"])
        self.assertTrue(result["startAvailable"])
        self.assertTrue(result["jamStep"])
        self.assertEqual("blocked", result["jamStatus"])
        self.assertEqual("material-jam", result["jamFault"])
        self.assertTrue(result["recoverAvailable"])
        self.assertEqual("recovering", result["recoveringStatus"])
        self.assertEqual("assigned", result["recoveredStatus"])
        self.assertEqual("restart-forge-line", result["recoveredStep"])
        self.assertEqual("idle", result["finalLaneStatus"])
        self.assertEqual(3, result["producedCircuits"])
        self.assertEqual("summary", result["tutorialStatus"])
        self.assertTrue(result["tutorialCompleted"])
        self.assertEqual("complete", result["tutorialContractStatus"])
        self.assertEqual("summary", result["shiftStatus"])
        self.assertTrue(result["summaryOpen"])
        self.assertEqual("available", result["upgradeChoiceStatus"])
        self.assertEqual([], result["contextualActionIds"])

    def test_tutorial_completion_persists_and_later_shift_unlocks_advanced_access(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/dark-factory-dispatch/dark-factory-dispatch.js");
            const bucket = {};
            const storage = {
              getItem(key) {
                return Object.prototype.hasOwnProperty.call(bucket, key) ? bucket[key] : null;
              },
              setItem(key, value) {
                bucket[key] = String(value);
              },
              removeItem(key) {
                delete bucket[key];
              },
            };

            let state = game.createInitialState({ seed: 91, storage });
            state = game.completeTutorial(state, storage);
            const restored = game.createInitialState({ seed: 91, storage });
            const later = game.createInitialState({ seed: 91, run: 2, storage });

            console.log(JSON.stringify({
              storedValue: bucket[state.tutorial.storageKey],
              persistedFlag: state.tutorial.completionPersisted,
              restoredCompleted: restored.tutorial.completed,
              restoredBeginnerVisible: restored.disclosure.beginnerVisible,
              restoredUpgradeVisible: restored.disclosure.systems.upgrades.visible,
              laterGridVisible: later.disclosure.systems.gridSiege.visible,
              laterBreachVisible: later.disclosure.systems.signalBreach.visible,
              laterFreightVisible: later.disclosure.systems.freightLockdown.visible,
              laterRailVisible: later.disclosure.systems.railSabotage.visible,
              laterCrisisVisible: later.disclosure.systems.crisisArbitration.visible,
              laterCrisisCases: game.crisisArbitrationSurfaceState(later).cases.length,
            }));
            """
        )

        self.assertEqual("complete", result["storedValue"])
        self.assertTrue(result["persistedFlag"])
        self.assertTrue(result["restoredCompleted"])
        self.assertFalse(result["restoredBeginnerVisible"])
        self.assertTrue(result["restoredUpgradeVisible"])
        self.assertTrue(result["laterGridVisible"])
        self.assertTrue(result["laterBreachVisible"])
        self.assertTrue(result["laterFreightVisible"])
        self.assertTrue(result["laterRailVisible"])
        self.assertTrue(result["laterCrisisVisible"])
        self.assertGreaterEqual(result["laterCrisisCases"], 2)

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
