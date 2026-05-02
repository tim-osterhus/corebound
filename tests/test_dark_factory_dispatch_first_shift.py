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

    def test_training_shift_wait_keeps_tutorial_recoverable_and_advanced_systems_idle(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/dark-factory-dispatch/dark-factory-dispatch.js");
            const advancedSnapshot = (state) => ({
              grid: {
                pressure: state.grid.pressure,
                currentLoad: state.grid.currentLoad,
                auditStatus: state.grid.audit.status,
                blackoutEvents: state.grid.blackout.events.length,
              },
              breach: {
                status: state.breach.status,
                intensity: state.breach.intensity,
                traceStatus: state.breach.trace.status,
                historyEvents: state.breach.history.length,
              },
              freight: state.freight.manifests.map((manifest) => ({
                id: manifest.id,
                status: manifest.status,
                openedAtTick: manifest.openedAtTick,
                outcome: manifest.outcome,
                inspectionStatus: manifest.inspection.status,
              })),
              rail: state.railSabotage.incidents.map((incident) => ({
                id: incident.id,
                status: incident.status,
                openedAtTick: incident.openedAtTick,
                outcome: incident.outcome,
                dockLocked: incident.dock.locked,
                scanStatus: incident.scan.status,
              })),
              crisis: state.crisisArbitration.cases.map((caseState) => ({
                id: caseState.id,
                status: caseState.status,
                openedAtTick: caseState.openedAtTick,
                outcome: caseState.outcome,
                dueTick: caseState.dueTick,
              })),
            });
            const advancedLogTerms = [
              "Grid",
              "Breach",
              "Freight",
              "Rail",
              "Crisis",
              "Docket",
              "Sabotage",
              "blackout",
              "manifest",
              "arbitration",
            ];

            let state = game.createInitialState({ seed: 1972, faultGraceTicks: 0 });
            const beforeAdvanced = advancedSnapshot(state);
            const smeltEntry = state.queue.find((entry) => entry.jobTypeId === "smelt-circuits");
            state = game.selectJobCard(state, smeltEntry.id);
            state = game.selectLane(state, "forge-line");
            state = game.performContextAction(state, "assign");
            state = game.performContextAction(state, "start");
            state = game.stepFactory(state, 12);
            const lane = state.lanes.find((candidate) => candidate.id === "forge-line");
            const recoverAction = state.contextualActions.find((action) => action.id === "recover");
            const advancedVisible = {
              grid: state.disclosure.systems.gridSiege.visible,
              breach: state.disclosure.systems.signalBreach.visible,
              freight: state.disclosure.systems.freightLockdown.visible,
              rail: state.disclosure.systems.railSabotage.visible,
              crisis: state.disclosure.systems.crisisArbitration.visible,
            };
            const advancedLogEntries = state.log
              .filter((entry) => advancedLogTerms.some((term) => entry.message.includes(term)))
              .map((entry) => entry.message);

            console.log(JSON.stringify({
              tick: state.tick,
              tutorialStatus: state.tutorial.status,
              tutorialCompleted: state.tutorial.completed,
              tutorialStep: state.tutorial.stepId,
              tutorialContractStatus: state.tutorial.contract.status,
              tutorialTimeRemaining: state.tutorial.contract.timeRemaining,
              shiftObjectiveTimeRemaining: state.shift.objective.timeRemaining,
              runStatus: state.run.status,
              failedContracts: state.run.failedContracts,
              laneStatus: lane.status,
              laneFault: lane.fault && lane.fault.id,
              laneGridLocked: Boolean(lane.gridLock),
              recoverAvailable: recoverAction && recoverAction.available,
              beforeAdvanced,
              afterAdvanced: advancedSnapshot(state),
              advancedVisible,
              advancedLogEntries,
            }));
            """
        )

        self.assertEqual(12, result["tick"])
        self.assertEqual("active", result["tutorialStatus"])
        self.assertFalse(result["tutorialCompleted"])
        self.assertEqual("recover-material-jam", result["tutorialStep"])
        self.assertEqual("active", result["tutorialContractStatus"])
        self.assertEqual(12, result["tutorialTimeRemaining"])
        self.assertEqual(12, result["shiftObjectiveTimeRemaining"])
        self.assertEqual("active", result["runStatus"])
        self.assertEqual(0, result["failedContracts"])
        self.assertEqual("blocked", result["laneStatus"])
        self.assertEqual("material-jam", result["laneFault"])
        self.assertFalse(result["laneGridLocked"])
        self.assertTrue(result["recoverAvailable"])
        self.assertEqual(result["beforeAdvanced"], result["afterAdvanced"])
        self.assertTrue(all(visible is False for visible in result["advancedVisible"].values()))
        self.assertEqual([], result["advancedLogEntries"])

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
              shiftObjectiveName: state.shift.objective.name,
              summaryOpen: Boolean(state.shift.summary),
              summaryProducedCircuits: state.shift.summary && state.shift.summary.produced.circuits,
              summaryResourceChangeRep: state.shift.summary && state.shift.summary.resourceChanges.reputation,
              summaryIncidentStatus: state.shift.summary && state.shift.summary.incident.status,
              summaryNextShift: state.shift.summary && state.shift.summary.nextShiftPreview.shift,
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
        self.assertEqual("Training Shift", result["shiftObjectiveName"])
        self.assertTrue(result["summaryOpen"])
        self.assertEqual(3, result["summaryProducedCircuits"])
        self.assertEqual(1, result["summaryResourceChangeRep"])
        self.assertEqual("resolved", result["summaryIncidentStatus"])
        self.assertEqual(2, result["summaryNextShift"])
        self.assertEqual("available", result["upgradeChoiceStatus"])
        self.assertEqual(["start-next-shift"], result["contextualActionIds"])

    def test_training_shift_summary_hold_blocks_advanced_pressure_until_handoff(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/dark-factory-dispatch/dark-factory-dispatch.js");
            const advancedSnapshot = (state) => ({
              grid: {
                pressure: state.grid.pressure,
                currentLoad: state.grid.currentLoad,
                auditStatus: state.grid.audit.status,
                blackoutEvents: state.grid.blackout.events.length,
              },
              breach: {
                status: state.breach.status,
                intensity: state.breach.intensity,
                traceStatus: state.breach.trace.status,
                historyEvents: state.breach.history.length,
              },
              freight: state.freight.manifests.map((manifest) => ({
                id: manifest.id,
                status: manifest.status,
                openedAtTick: manifest.openedAtTick,
                outcome: manifest.outcome,
                inspectionStatus: manifest.inspection.status,
              })),
              rail: state.railSabotage.incidents.map((incident) => ({
                id: incident.id,
                status: incident.status,
                openedAtTick: incident.openedAtTick,
                outcome: incident.outcome,
                dockLocked: incident.dock.locked,
                scanStatus: incident.scan.status,
              })),
              crisis: state.crisisArbitration.cases.map((caseState) => ({
                id: caseState.id,
                status: caseState.status,
                openedAtTick: caseState.openedAtTick,
                outcome: caseState.outcome,
                dueTick: caseState.dueTick,
              })),
            });
            const factoryRating = (state) => {
              const activeFaults = state.lanes.filter((lane) => lane.fault || lane.status === "locked").length;
              return Math.max(0, Math.min(99, state.resources.stability - activeFaults * 6 + state.resources.reputation * 3));
            };
            const advancedLogTerms = [
              "Grid",
              "Breach",
              "Freight",
              "Rail",
              "Crisis",
              "Docket",
              "Sabotage",
              "blackout",
              "manifest",
              "arbitration",
            ];

            let state = game.createInitialState({ seed: 1972, faultGraceTicks: 0 });
            const smeltEntry = state.queue.find((entry) => entry.jobTypeId === "smelt-circuits");
            state = game.selectJobCard(state, smeltEntry.id);
            state = game.selectLane(state, "forge-line");
            state = game.performContextAction(state, "assign");
            state = game.performContextAction(state, "start");
            state = game.stepFactory(state, 1);
            state = game.performContextAction(state, "recover");
            state = game.stepFactory(state, state.lanes.find((lane) => lane.id === "forge-line").recoveryRemaining);
            state = game.performContextAction(state, "start");
            state = game.stepFactory(state, state.lanes.find((lane) => lane.id === "forge-line").currentJob.remaining);

            const holdOpen = {
              tick: state.tick,
              objectiveName: state.shift.objective.name,
              objectiveStatus: state.shift.objective.status,
              objectiveTimeRemaining: state.shift.objective.timeRemaining,
              summaryStatus: state.shift.summary.status,
              summaryProduced: state.shift.summary.produced,
              summaryResources: state.shift.summary.resources,
              summaryResourceChanges: state.shift.summary.resourceChanges,
              summaryIncident: state.shift.summary.incident,
              summaryNextShift: state.shift.summary.nextShiftPreview,
              handoffAction: state.contextualActions.find((action) => action.id === "start-next-shift"),
              advanced: advancedSnapshot(state),
              rating: factoryRating(state),
              laneGridLock: Boolean(state.lanes.find((lane) => lane.id === "forge-line").gridLock),
              contractStatuses: state.contracts.map((contract) => ({
                id: contract.id,
                status: contract.status,
                timeRemaining: contract.timeRemaining,
              })),
            };

            state = game.stepFactory(state, 15);
            const holdAfterWait = {
              tick: state.tick,
              objectiveName: state.shift.objective.name,
              objectiveStatus: state.shift.objective.status,
              objectiveTimeRemaining: state.shift.objective.timeRemaining,
              summaryStatus: state.shift.summary.status,
              summaryProduced: state.shift.summary.produced,
              summaryResources: state.shift.summary.resources,
              summaryResourceChanges: state.shift.summary.resourceChanges,
              summaryIncident: state.shift.summary.incident,
              advanced: advancedSnapshot(state),
              rating: factoryRating(state),
              laneGridLock: Boolean(state.lanes.find((lane) => lane.id === "forge-line").gridLock),
              contractStatuses: state.contracts.map((contract) => ({
                id: contract.id,
                status: contract.status,
                timeRemaining: contract.timeRemaining,
              })),
              advancedVisible: {
                grid: state.disclosure.systems.gridSiege.visible,
                breach: state.disclosure.systems.signalBreach.visible,
                freight: state.disclosure.systems.freightLockdown.visible,
                rail: state.disclosure.systems.railSabotage.visible,
                crisis: state.disclosure.systems.crisisArbitration.visible,
              },
              advancedLogEntries: state.log
                .filter((entry) => advancedLogTerms.some((term) => entry.message.includes(term)))
                .map((entry) => entry.message),
              handoffAction: state.contextualActions.find((action) => action.id === "start-next-shift"),
            };

            const nextShift = game.performContextAction(state, "start-next-shift");

            console.log(JSON.stringify({
              holdOpen,
              holdAfterWait,
              nextShiftRun: nextShift.restart.run,
              nextShiftSummaryOpen: Boolean(nextShift.shift.summary),
              nextShiftGridVisible: nextShift.disclosure.systems.gridSiege.visible,
              nextShiftBreachVisible: nextShift.disclosure.systems.signalBreach.visible,
              nextShiftFreightVisible: nextShift.disclosure.systems.freightLockdown.visible,
              nextShiftRailVisible: nextShift.disclosure.systems.railSabotage.visible,
              nextShiftCrisisVisible: nextShift.disclosure.systems.crisisArbitration.visible,
            }));
            """
        )

        opened = result["holdOpen"]
        waited = result["holdAfterWait"]

        self.assertEqual("Training Shift", opened["objectiveName"])
        self.assertEqual("complete", opened["objectiveStatus"])
        self.assertEqual("complete", opened["summaryStatus"])
        self.assertEqual(3, opened["summaryProduced"]["circuits"])
        self.assertGreater(opened["summaryResources"]["reputation"], 0)
        self.assertEqual({"reputation": 1}, opened["summaryResourceChanges"])
        self.assertEqual("resolved", opened["summaryIncident"]["status"])
        self.assertEqual(2, opened["summaryNextShift"]["shift"])
        self.assertEqual("start-next-shift", opened["handoffAction"]["id"])

        self.assertEqual(opened["tick"] + 15, waited["tick"])
        self.assertEqual("Training Shift", waited["objectiveName"])
        self.assertEqual(opened["objectiveStatus"], waited["objectiveStatus"])
        self.assertEqual(opened["objectiveTimeRemaining"], waited["objectiveTimeRemaining"])
        self.assertEqual(opened["summaryProduced"], waited["summaryProduced"])
        self.assertEqual(opened["summaryResources"], waited["summaryResources"])
        self.assertEqual(opened["summaryResourceChanges"], waited["summaryResourceChanges"])
        self.assertEqual(opened["summaryIncident"], waited["summaryIncident"])
        self.assertEqual(opened["advanced"], waited["advanced"])
        self.assertEqual(opened["rating"], waited["rating"])
        self.assertEqual(opened["laneGridLock"], waited["laneGridLock"])
        self.assertEqual(opened["contractStatuses"], waited["contractStatuses"])
        self.assertTrue(all(visible is False for visible in waited["advancedVisible"].values()))
        self.assertEqual([], waited["advancedLogEntries"])
        self.assertEqual("start-next-shift", waited["handoffAction"]["id"])

        self.assertEqual(2, result["nextShiftRun"])
        self.assertFalse(result["nextShiftSummaryOpen"])
        self.assertTrue(result["nextShiftGridVisible"])
        self.assertTrue(result["nextShiftBreachVisible"])
        self.assertTrue(result["nextShiftFreightVisible"])
        self.assertTrue(result["nextShiftRailVisible"])
        self.assertTrue(result["nextShiftCrisisVisible"])

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
