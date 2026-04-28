import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_manifest() -> dict:
    return json.loads((ROOT / "data" / "games.json").read_text(encoding="utf-8"))


def game_by_slug(slug: str) -> dict:
    for game in load_manifest()["games"]:
        if game.get("slug") == slug:
            return game
    raise AssertionError(f"missing manifest game {slug}")


class VoidProspectorArcadeReleaseTests(unittest.TestCase):
    def test_manifest_adds_truthful_void_prospector_survey_ladder_release(self) -> None:
        game = game_by_slug("void-prospector")

        self.assertEqual("Void Prospector", game["title"])
        self.assertEqual("0.1.0", game["version"])
        self.assertEqual("playable", game["status"])
        self.assertEqual("games/void-prospector/", game["path"])
        self.assertEqual("games/void-prospector/assets/arcade-title-card.png", game["thumbnail"])
        self.assertIn("Prospector Kite", game["summary"])
        self.assertIn("three-tier Survey Ladder", game["summary"])
        self.assertIn("anomaly scans", game["summary"])
        self.assertIn("station probe and decoy services", game["summary"])
        self.assertIn("pirate escalation", game["summary"])
        self.assertEqual("v0.1.0 Survey Ladder", game["release"]["label"])
        self.assertIn("three-sector campaign", game["release"]["copy"])
        self.assertIn("Rift Shelf", game["release"]["copy"])
        self.assertIn("Umbra Trench", game["release"]["copy"])
        self.assertIn("sector route selection", game["release"]["copy"])

        self.assertNotIn("snapshot", game)
        current_snapshot = game["versions"][0]
        self.assertEqual("0.1.0", current_snapshot["version"])
        self.assertEqual("games/void-prospector/versions/0.1.0/", current_snapshot["path"])
        self.assertEqual("2026-04-28", current_snapshot["releasedAt"])
        self.assertEqual("v0.1.0 Survey Ladder", current_snapshot["label"])
        self.assertIn("Three-sector Survey Ladder campaign", current_snapshot["summary"])
        self.assertIn("anomaly scans", current_snapshot["summary"])
        self.assertIn("station probe and decoy services", current_snapshot["summary"])
        self.assertRegex(current_snapshot["commit"], r"^[0-9a-f]{40}$")

        first_snapshot = game["versions"][1]
        self.assertEqual("0.0.1", first_snapshot["version"])
        self.assertEqual("games/void-prospector/versions/0.0.1/", first_snapshot["path"])
        self.assertEqual("v0.0.1 First Sortie", first_snapshot["label"])

    def test_manifest_preserves_existing_games_while_listing_three_games(self) -> None:
        manifest = load_manifest()
        slugs = [game["slug"] for game in manifest["games"]]

        self.assertEqual(["corebound", "dark-factory-dispatch", "void-prospector"], slugs)
        self.assertEqual("0.7.0", game_by_slug("corebound")["version"])
        self.assertEqual("0.1.0", game_by_slug("dark-factory-dispatch")["version"])
        self.assertEqual("0.1.0", game_by_slug("void-prospector")["version"])

    def test_generated_arcade_output_lists_survey_ladder_card_snapshots_and_thumbnail(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn("games <strong>3 games</strong>", html)
        self.assertIn("Corebound", html)
        self.assertIn("Dark Factory Dispatch", html)
        self.assertIn("Void Prospector", html)
        self.assertIn('href="games/corebound/"', html)
        self.assertIn('href="games/dark-factory-dispatch/"', html)
        self.assertIn('href="games/void-prospector/"', html)
        self.assertIn('src="games/void-prospector/assets/arcade-title-card.png"', html)
        self.assertIn("playable / v0.1.0", html)
        self.assertIn("v0.1.0 Survey Ladder", html)
        self.assertIn("three-tier Survey Ladder", html)
        self.assertIn("anomaly scans", html)
        self.assertIn("sector route selection", html)
        self.assertIn("Snapshots", html)
        self.assertIn('href="games/void-prospector/versions/0.1.0/"', html)
        self.assertIn('href="games/void-prospector/versions/0.0.1/"', html)
        self.assertIn("v0.0.1 First Sortie", html)
        self.assertIn("commit ", html)
        self.assertNotIn("Commit-backed Void Prospector snapshot", html)
        self.assertNotIn("Snapshot deferred", html)

    def test_snapshot_directory_preserves_playable_static_survey_ladder_release(self) -> None:
        snapshot_dir = ROOT / "games" / "void-prospector" / "versions" / "0.1.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "void-prospector.js").read_text(encoding="utf-8")

        self.assertIn("<title>Void Prospector</title>", html)
        self.assertIn("void-prospector.css", html)
        self.assertIn("void-prospector.js", html)
        self.assertIn("v0.1.0 Survey Ladder", html)
        self.assertIn("survey-panel", html)
        self.assertIn("scan-action", html)
        self.assertIn('src="assets/arcade-title-card.png"', html)
        self.assertIn('src="vendor/three.min.js"', html)
        self.assertIn('releaseLabel: "Survey Ladder"', script)
        self.assertIn("Rift Shelf", script)
        self.assertIn("Umbra Trench", script)
        self.assertIn("scanTarget", script)
        self.assertIn("chooseSector", script)
        self.assertIn("purchaseStationService", script)
        self.assertIn("deployCountermeasure", script)
        self.assertNotIn("/versions/", script)
        self.assertFalse((snapshot_dir / "versions").exists())
        self.assertTrue((snapshot_dir / "assets" / "arcade-title-card.png").is_file())
        self.assertTrue((snapshot_dir / "assets" / "asset-manifest.json").is_file())
        self.assertTrue((snapshot_dir / "vendor" / "three.min.js").is_file())
        self.assertRegex(game_by_slug("void-prospector")["versions"][0]["commit"], r"^[0-9a-f]{40}$")

    def test_first_sortie_snapshot_remains_available_after_survey_ladder_release(self) -> None:
        game = game_by_slug("void-prospector")
        snapshot_dir = ROOT / "games" / "void-prospector" / "versions" / "0.0.1"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "void-prospector.js").read_text(encoding="utf-8")

        self.assertEqual("0.0.1", game["versions"][1]["version"])
        self.assertEqual("games/void-prospector/versions/0.0.1/", game["versions"][1]["path"])
        self.assertIn("<title>Void Prospector</title>", html)
        self.assertIn("First Sortie", game["versions"][1]["label"])
        self.assertNotIn("/versions/", script)


if __name__ == "__main__":
    unittest.main()
