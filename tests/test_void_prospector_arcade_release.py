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
    def test_manifest_adds_truthful_void_prospector_beacon_convoy_release(self) -> None:
        game = game_by_slug("void-prospector")

        self.assertEqual("Void Prospector", game["title"])
        self.assertEqual("0.3.0", game["version"])
        self.assertEqual("playable", game["status"])
        self.assertEqual("games/void-prospector/", game["path"])
        self.assertEqual("games/void-prospector/assets/arcade-title-card.png", game["thumbnail"])
        self.assertIn("Prospector Kite", game["summary"])
        self.assertIn("Survey Ladder sectors", game["summary"])
        self.assertIn("anomaly scans", game["summary"])
        self.assertIn("salvage extraction", game["summary"])
        self.assertIn("deployable route beacons", game["summary"])
        self.assertIn("convoy contracts", game["summary"])
        self.assertIn("escort integrity", game["summary"])
        self.assertIn("pirate interdiction", game["summary"])
        self.assertIn("station escort drones", game["summary"])
        self.assertIn("signal jammers", game["summary"])
        self.assertIn("countermeasure bursts", game["summary"])
        self.assertEqual("v0.3.0 Beacon Convoy", game["release"]["label"])
        self.assertIn("deployable route beacons", game["release"]["copy"])
        self.assertIn("escort runs", game["release"]["copy"])
        self.assertIn("deploy or maintain relay beacons", game["release"]["copy"])
        self.assertIn("launch cargo convoys", game["release"]["copy"])
        self.assertIn("ambush and hazard pressure", game["release"]["copy"])
        self.assertIn("escort drones or signal jammers", game["release"]["copy"])
        self.assertIn("full or partial payouts", game["release"]["copy"])

        self.assertNotIn("snapshot", game)
        current_snapshot = game["versions"][0]
        self.assertEqual("0.3.0", current_snapshot["version"])
        self.assertEqual("games/void-prospector/versions/0.3.0/", current_snapshot["path"])
        self.assertEqual("2026-04-29", current_snapshot["releasedAt"])
        self.assertEqual("v0.3.0 Beacon Convoy", current_snapshot["label"])
        self.assertIn("Deployable route beacons", current_snapshot["summary"])
        self.assertIn("convoy cargo runs", current_snapshot["summary"])
        self.assertIn("escort integrity", current_snapshot["summary"])
        self.assertIn("station escort drones", current_snapshot["summary"])
        self.assertIn("countermeasure bursts", current_snapshot["summary"])
        self.assertNotIn("commit", current_snapshot)

        salvage_snapshot = game["versions"][1]
        self.assertEqual("0.2.0", salvage_snapshot["version"])
        self.assertEqual("games/void-prospector/versions/0.2.0/", salvage_snapshot["path"])
        self.assertEqual("v0.2.0 Derelict Salvage", salvage_snapshot["label"])

        survey_snapshot = game["versions"][2]
        self.assertEqual("0.1.0", survey_snapshot["version"])
        self.assertEqual("games/void-prospector/versions/0.1.0/", survey_snapshot["path"])
        self.assertEqual("v0.1.0 Survey Ladder", survey_snapshot["label"])

        first_snapshot = game["versions"][3]
        self.assertEqual("0.0.1", first_snapshot["version"])
        self.assertEqual("games/void-prospector/versions/0.0.1/", first_snapshot["path"])
        self.assertEqual("v0.0.1 First Sortie", first_snapshot["label"])

    def test_manifest_preserves_existing_games_while_listing_three_games(self) -> None:
        manifest = load_manifest()
        slugs = [game["slug"] for game in manifest["games"]]

        self.assertEqual(["corebound", "dark-factory-dispatch", "void-prospector"], slugs)
        self.assertEqual("0.7.0", game_by_slug("corebound")["version"])
        self.assertEqual("0.4.0", game_by_slug("dark-factory-dispatch")["version"])
        self.assertEqual("0.3.0", game_by_slug("void-prospector")["version"])

    def test_generated_arcade_output_lists_beacon_convoy_card_snapshots_and_thumbnail(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn("games <strong>3 games</strong>", html)
        self.assertIn("Corebound", html)
        self.assertIn("Dark Factory Dispatch", html)
        self.assertIn("Void Prospector", html)
        self.assertIn('href="games/corebound/"', html)
        self.assertIn('href="games/dark-factory-dispatch/"', html)
        self.assertIn('href="games/void-prospector/"', html)
        self.assertIn('src="games/void-prospector/assets/arcade-title-card.png"', html)
        self.assertIn("playable / v0.3.0", html)
        self.assertIn("v0.3.0 Beacon Convoy", html)
        self.assertIn("Survey Ladder sectors", html)
        self.assertIn("deployable route beacons", html)
        self.assertIn("convoy contracts", html)
        self.assertIn("station escort drones", html)
        self.assertIn("launch cargo convoys", html)
        self.assertIn("full or partial payouts", html)
        self.assertIn("Snapshots", html)
        self.assertIn('href="games/void-prospector/versions/0.3.0/"', html)
        self.assertIn("<span class=\"snapshot-meta\"><span>2026-04-29</span></span>", html)
        self.assertIn('href="games/void-prospector/versions/0.2.0/"', html)
        self.assertIn('href="games/void-prospector/versions/0.1.0/"', html)
        self.assertIn('href="games/void-prospector/versions/0.0.1/"', html)
        self.assertIn("v0.2.0 Derelict Salvage", html)
        self.assertIn("v0.1.0 Survey Ladder", html)
        self.assertIn("v0.0.1 First Sortie", html)
        self.assertIn("commit ", html)
        self.assertNotIn("Commit-backed Void Prospector snapshot", html)
        self.assertNotIn("Snapshot deferred", html)

    def test_snapshot_directory_preserves_playable_static_beacon_convoy_release(self) -> None:
        snapshot_dir = ROOT / "games" / "void-prospector" / "versions" / "0.3.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "void-prospector.js").read_text(encoding="utf-8")

        self.assertIn("<title>Void Prospector</title>", html)
        self.assertIn("void-prospector.css", html)
        self.assertIn("void-prospector.js", html)
        self.assertIn("v0.3.0 Beacon Convoy", html)
        self.assertIn("survey-panel", html)
        self.assertIn("salvage-target-data", html)
        self.assertIn("convoy-target-data", html)
        self.assertIn("convoy-list", html)
        self.assertIn("beacon-action", html)
        self.assertIn("convoy-action", html)
        self.assertIn("service-escort-action", html)
        self.assertIn("service-jammers-action", html)
        self.assertIn("countermeasure-action", html)
        self.assertIn('src="assets/arcade-title-card.png"', html)
        self.assertIn('src="vendor/three.min.js"', html)
        self.assertIn('releaseLabel: "Beacon Convoy"', script)
        self.assertIn("convoy-rift-relay", script)
        self.assertIn("convoy-umbra-blackbox", script)
        self.assertIn("deployRouteBeacon", script)
        self.assertIn("startConvoyRoute", script)
        self.assertIn("advanceConvoyRoute", script)
        self.assertIn("deployConvoyCountermeasure", script)
        self.assertIn("purchaseStationService", script)
        self.assertNotIn("/versions/", script)
        self.assertFalse((snapshot_dir / "versions").exists())
        self.assertTrue((snapshot_dir / "assets" / "arcade-title-card.png").is_file())
        self.assertTrue((snapshot_dir / "assets" / "asset-manifest.json").is_file())
        self.assertTrue((snapshot_dir / "vendor" / "three.min.js").is_file())
        self.assertNotIn("commit", game_by_slug("void-prospector")["versions"][0])

    def test_derelict_salvage_snapshot_remains_available_after_beacon_convoy_release(self) -> None:
        game = game_by_slug("void-prospector")
        snapshot_dir = ROOT / "games" / "void-prospector" / "versions" / "0.2.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "void-prospector.js").read_text(encoding="utf-8")

        self.assertEqual("0.2.0", game["versions"][1]["version"])
        self.assertEqual("games/void-prospector/versions/0.2.0/", game["versions"][1]["path"])
        self.assertIn("<title>Void Prospector</title>", html)
        self.assertIn("v0.2.0 Derelict Salvage", html)
        self.assertIn('releaseLabel: "Derelict Salvage"', script)
        self.assertIn("salvage-rift-hulk", script)
        self.assertIn("salvage-rift-volatile", script)
        self.assertIn("salvage-umbra-vault", script)
        self.assertIn("scanSalvageTarget", script)
        self.assertIn("extractSalvageTarget", script)
        self.assertIn("purchaseStationService", script)
        self.assertNotIn("convoy-rift-relay", script)
        self.assertNotIn("/versions/", script)

    def test_survey_ladder_snapshot_remains_available_after_beacon_convoy_release(self) -> None:
        game = game_by_slug("void-prospector")
        snapshot_dir = ROOT / "games" / "void-prospector" / "versions" / "0.1.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "void-prospector.js").read_text(encoding="utf-8")

        self.assertEqual("0.1.0", game["versions"][2]["version"])
        self.assertEqual("games/void-prospector/versions/0.1.0/", game["versions"][2]["path"])
        self.assertIn("<title>Void Prospector</title>", html)
        self.assertIn("v0.1.0 Survey Ladder", html)
        self.assertIn('releaseLabel: "Survey Ladder"', script)
        self.assertIn("Rift Shelf", script)
        self.assertIn("Umbra Trench", script)
        self.assertIn("scanTarget", script)
        self.assertIn("chooseSector", script)
        self.assertIn("deployCountermeasure", script)
        self.assertNotIn("salvage-rift-hulk", script)
        self.assertNotIn("convoy-rift-relay", script)
        self.assertNotIn("/versions/", script)

    def test_first_sortie_snapshot_remains_available_after_beacon_convoy_release(self) -> None:
        game = game_by_slug("void-prospector")
        snapshot_dir = ROOT / "games" / "void-prospector" / "versions" / "0.0.1"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "void-prospector.js").read_text(encoding="utf-8")

        self.assertEqual("0.0.1", game["versions"][3]["version"])
        self.assertEqual("games/void-prospector/versions/0.0.1/", game["versions"][3]["path"])
        self.assertIn("<title>Void Prospector</title>", html)
        self.assertIn("First Sortie", game["versions"][3]["label"])
        self.assertNotIn("salvage-rift-hulk", script)
        self.assertNotIn("convoy-rift-relay", script)
        self.assertNotIn("/versions/", script)


if __name__ == "__main__":
    unittest.main()
