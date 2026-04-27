import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "corebound"


class CoreboundObjectiveArchiveTests(unittest.TestCase):
    def test_hud_exposes_contract_and_archive_surfaces(self) -> None:
        html = (GAME_DIR / "index.html").read_text(encoding="utf-8")

        for surface_id in (
            "contract-status",
            "contract-progress",
            "contract-list",
            "archive-status",
            "archive-list",
        ):
            self.assertIn(surface_id, html)
        self.assertIn("Run contracts", html)
        self.assertIn("Relic archive", html)

    def test_objectives_and_archive_sets_are_data_driven(self) -> None:
        data = (GAME_DIR / "corebound-data.js").read_text(encoding="utf-8")

        self.assertIn("contracts", data)
        self.assertIn("archiveSets", data)
        for contract_id in ("siltSurvey", "saltglassAssay", "deepLedgerRecovery"):
            self.assertIn(contract_id, data)
        for contract_kind in ('kind: "depth"', 'kind: "ore"', 'kind: "archive"'):
            self.assertIn(contract_kind, data)
        for archive_id in ("surfaceRelay", "deepLedger"):
            self.assertIn(archive_id, data)
        self.assertIn("archiveFragments", data)
        self.assertIn("fragmentsRequired", data)
        self.assertIn("effects: { moveEnergy: -0.06, archiveSignal: 1 }", data)
        self.assertIn("archive: { set: \"deepLedger\", fragments: 1 }", data)

    def test_game_loop_tracks_contract_progress_completion_and_archive_unlocks(self) -> None:
        script = (GAME_DIR / "corebound.js").read_text(encoding="utf-8")

        for behavior in (
            "acceptContract",
            "activeContract",
            "updateContractProgress",
            "completeActiveContract",
            "rewardContract",
            "renderContractPanel",
            "applyArchiveFragments",
            "archiveFragmentsFromCargo",
            "noteArchiveContractProgress",
            "renderArchivePanel",
            "archiveProgressFor",
        ):
            self.assertIn(behavior, script)
        self.assertIn("state.completedContracts[contract.id] = true", script)
        self.assertIn("state.activeContractId = null", script)
        self.assertIn("applyStatEffects(stats, archiveSet.unlock.effects)", script)
        self.assertIn("state.player.y * DATA.world.metersPerTile", script)
        self.assertIn("button.addEventListener(\"click\", () => acceptContract(entry.id))", script)


if __name__ == "__main__":
    unittest.main()
