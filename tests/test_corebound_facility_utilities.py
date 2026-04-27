import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "corebound"


class CoreboundFacilityUtilityTests(unittest.TestCase):
    def test_hud_exposes_reputation_facility_and_utility_controls(self) -> None:
        html = (GAME_DIR / "index.html").read_text(encoding="utf-8")

        for surface_id in (
            "facility-status",
            "facility-progress",
            "utility-list",
        ):
            self.assertIn(surface_id, html)
        self.assertIn("Facility reputation and utilities", html)
        self.assertIn("File contracts to arm route support", html)

    def test_reputation_facility_and_utilities_are_data_driven(self) -> None:
        data = (GAME_DIR / "corebound-data.js").read_text(encoding="utf-8")

        self.assertIn("reputationTracks", data)
        self.assertIn("utilities", data)
        self.assertIn("surveyRelay", data)
        for rank_id in ("candidate", "filedRoute", "sigilRelay"):
            self.assertIn(rank_id, data)
        for utility_id in ("sweepScan", "routeBeacon", "coolantBurst"):
            self.assertIn(utility_id, data)
        self.assertIn("requires: { contracts: 1, archiveSets: 0 }", data)
        self.assertIn("requires: { contracts: 1, archiveSets: 1 }", data)
        self.assertIn("effects: { scanRange: 1, beaconCharges: 1, beaconReturnEfficiency: 0.35 }", data)
        self.assertIn("effects: { scanRange: 1, coolantCharges: 1, utilityCooling: 16 }", data)
        self.assertIn('requiresRank: "filedRoute"', data)
        self.assertIn('requiresRank: "sigilRelay"', data)

    def test_game_loop_applies_facility_ranks_and_utility_state_transitions(self) -> None:
        script = (GAME_DIR / "corebound.js").read_text(encoding="utf-8")

        for behavior in (
            "completedContractCount",
            "completedArchiveSetCount",
            "reputationRankFor",
            "utilityUnlocked",
            "utilityChargesRemaining",
            "runSweepScan",
            "deployRouteBeacon",
            "triggerCoolantBurst",
            "useUtility",
            "nearRouteBeacon",
            "renderFacilityPanel",
            "drawBeaconMark",
        ):
            self.assertIn(behavior, script)
        self.assertIn("for (const track of DATA.reputationTracks || [])", script)
        self.assertIn("applyStatEffects(stats, rank.effects)", script)
        self.assertIn("state.utilityUses[utility.id] =", script)
        self.assertIn("state.beacons.push({ x: state.player.x, y: state.player.y })", script)
        self.assertIn("moveCost *= Math.max(0.4, 1 - stats.beaconReturnEfficiency)", script)
        self.assertIn("state.heat = Math.max(0, state.heat - cooling)", script)
        self.assertIn("state.utilityUses = {}", script)
        self.assertIn("state.beacons = []", script)
        self.assertIn('button.addEventListener("click", () => useUtility(utility.id))', script)


if __name__ == "__main__":
    unittest.main()
