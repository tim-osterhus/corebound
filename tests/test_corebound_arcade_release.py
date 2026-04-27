import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "games.json"
INDEX_PATH = ROOT / "index.html"
GAME_DIR = ROOT / "games" / "corebound"


class CoreboundArcadeReleaseTests(unittest.TestCase):
    def test_manifest_registers_playable_corebound_release(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        games = manifest.get("games")

        self.assertIsInstance(games, list)
        corebound = next((game for game in games if game.get("slug") == "corebound"), None)
        self.assertIsNotNone(corebound)
        self.assertEqual("Corebound", corebound["title"])
        self.assertEqual("0.2.0", corebound["version"])
        self.assertEqual("playable", corebound["status"])
        self.assertEqual("games/corebound/", corebound["path"])
        self.assertIn("contracts", corebound["summary"])
        self.assertIn("archive", corebound["summary"])
        self.assertIn("Survey relay", corebound["summary"])
        self.assertIn("v0.2.0 continuity", corebound["release"]["label"])
        self.assertIn("coolant", corebound["release"]["copy"])
        self.assertTrue((GAME_DIR / "index.html").is_file())
        self.assertTrue((GAME_DIR / "corebound.js").is_file())
        self.assertTrue((GAME_DIR / "corebound-data.js").is_file())

    def test_manifest_documents_truthful_snapshot_deferral(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        corebound = next(game for game in manifest["games"] if game.get("slug") == "corebound")
        snapshot = corebound.get("snapshot")

        self.assertEqual("deferred", snapshot["status"])
        self.assertEqual("0.2.0", snapshot["version"])
        self.assertIn("uncommitted working-tree", snapshot["reason"])
        self.assertNotIn("commit", snapshot)
        self.assertNotIn("releasedAt", snapshot)
        self.assertNotIn("versions", corebound)

    def test_generated_arcade_links_to_corebound_build(self) -> None:
        index = INDEX_PATH.read_text(encoding="utf-8")

        self.assertIn("Corebound is playable.", index)
        self.assertIn("playable / v0.2.0", index)
        self.assertIn("games <strong>1 game</strong>", index)
        self.assertIn('href="games/corebound/"', index)
        self.assertIn("contracts, archive sets, Survey relay", index)
        self.assertIn("v0.2.0 continuity", index)
        self.assertIn("Snapshot deferred", index)
        self.assertIn("uncommitted working-tree", index)
        self.assertNotIn("No playable builds are listed yet", index)


if __name__ == "__main__":
    unittest.main()
