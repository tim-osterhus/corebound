import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "corebound"


class CoreboundDeepCharterTests(unittest.TestCase):
    def test_hud_exposes_named_deep_charter_selection_surface(self) -> None:
        html = (GAME_DIR / "index.html").read_text(encoding="utf-8")

        for surface_id in (
            "charter-status",
            "charter-progress",
            "charter-list",
        ):
            self.assertIn(surface_id, html)
        self.assertIn("Deep Charter", html)
        self.assertIn("Choose an expedition charter before launch", html)

    def test_deep_charters_are_data_driven_with_constraints_and_rewards(self) -> None:
        data = (GAME_DIR / "corebound-data.js").read_text(encoding="utf-8")

        self.assertIn("deepCharters", data)
        for charter_id in ("siltLineCharter", "thermalTraceCharter", "ledgerTitheCharter"):
            self.assertIn(charter_id, data)
        for key in ("objective", "constraint", "reward", "relayEffects"):
            self.assertIn(key, data)
        self.assertIn("effects: { maxEnergy: -12, returnEnergyPenalty: 0.12 }", data)
        self.assertIn("effects: { charterDrillHeat: 2, thermalShielding: -1 }", data)
        self.assertIn("effects: { cargoCapacity: -3, moveEnergy: 0.08 }", data)
        self.assertIn("archiveFragments: { surfaceRelay: 1 }", data)
        self.assertIn("archiveFragments: { deepLedger: 1 }", data)
        self.assertIn("relayEffects: { scanRange: 1, anchorCharges: 1 }", data)
        self.assertIn("relayEffects: { beaconCharges: 1, beaconReturnEfficiency: 0.08 }", data)

    def test_game_loop_tracks_selection_progress_completion_and_reward_seams(self) -> None:
        script = (GAME_DIR / "corebound.js").read_text(encoding="utf-8")

        for behavior in (
            "activeCharterId",
            "runCharterId",
            "completedCharters",
            "charterProgress",
            "acceptCharter",
            "selectedCharter",
            "runCharter",
            "visibleCharter",
            "updateCharterProgress",
            "completeRunCharter",
            "rewardCharter",
            "formatCharterReward",
            "formatRelayEffects",
            "renderCharterPanel",
        ):
            self.assertIn(behavior, script)
        self.assertIn("state.runCharterId = state.activeCharterId", script)
        self.assertIn("applyStatEffects(stats, charter.reward.relayEffects)", script)
        self.assertIn("applyStatEffects(stats, activeCharter.constraint.effects)", script)
        self.assertIn("state.completedCharters[charter.id] = true", script)
        self.assertIn("state.activeCharterId = null", script)
        self.assertIn("state.player.y * DATA.world.metersPerTile", script)
        self.assertIn("state.cargo.filter((oreKey) => oreKey === objective.ore).length", script)
        self.assertIn("terrain.heat || 0) + pressure + stats.charterDrillHeat", script)
        self.assertIn("moveCost *= 1 + stats.returnEnergyPenalty", script)
        self.assertIn('button.addEventListener("click", () => acceptCharter(entry.id))', script)


if __name__ == "__main__":
    unittest.main()
