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


class DarkFactoryDispatchArcadeReleaseTests(unittest.TestCase):
    def test_manifest_adds_truthful_dark_factory_dispatch_grid_siege_release(self) -> None:
        game = game_by_slug("dark-factory-dispatch")

        self.assertEqual("Dark Factory Dispatch", game["title"])
        self.assertEqual("0.2.0", game["version"])
        self.assertEqual("playable", game["status"])
        self.assertEqual("games/dark-factory-dispatch/", game["path"])
        self.assertEqual("games/dark-factory-dispatch/assets/arcade-title-card.png", game["thumbnail"])
        self.assertIn("Grid Siege shifts", game["summary"])
        self.assertIn("facility power routing", game["summary"])
        self.assertIn("reserve batteries", game["summary"])
        self.assertIn("blackout lockouts", game["summary"])
        self.assertIn("audit relay directives", game["summary"])
        self.assertIn("emergency coolant-diversion orders", game["summary"])
        self.assertIn("lane overdrive calls", game["summary"])
        self.assertEqual("v0.2.0 Grid Siege", game["release"]["label"])
        self.assertIn("facility power-grid layer", game["release"]["copy"])
        self.assertIn("route priority power", game["release"]["copy"])
        self.assertIn("isolate threatened sectors", game["release"]["copy"])
        self.assertIn("Reserve Ledger Audit directives", game["release"]["copy"])
        self.assertIn("Escalation Shift emergency queue", game["release"]["copy"])

        self.assertNotIn("snapshot", game)
        current_snapshot = game["versions"][0]
        self.assertEqual("0.2.0", current_snapshot["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.2.0/", current_snapshot["path"])
        self.assertEqual("2026-04-28", current_snapshot["releasedAt"])
        self.assertEqual("v0.2.0 Grid Siege", current_snapshot["label"])
        self.assertIn("Facility power routing", current_snapshot["summary"])
        self.assertIn("blackout lockouts", current_snapshot["summary"])
        self.assertIn("Reserve Ledger Audit directives", current_snapshot["summary"])
        self.assertRegex(current_snapshot["commit"], r"^[0-9a-f]{40}$")

        escalation_snapshot = game["versions"][1]
        self.assertEqual("0.1.0", escalation_snapshot["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.1.0/", escalation_snapshot["path"])
        self.assertEqual("v0.1.0 Escalation Shift", escalation_snapshot["label"])

        first_snapshot = game["versions"][2]
        self.assertEqual("0.0.1", first_snapshot["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.0.1/", first_snapshot["path"])
        self.assertEqual("v0.0.1 Dispatch Floor", first_snapshot["label"])

    def test_manifest_preserves_corebound_while_listing_three_games(self) -> None:
        manifest = load_manifest()
        slugs = [game["slug"] for game in manifest["games"]]

        self.assertIn("corebound", slugs)
        self.assertIn("dark-factory-dispatch", slugs)
        self.assertIn("void-prospector", slugs)
        self.assertEqual(3, len(slugs))
        self.assertEqual("0.7.0", game_by_slug("corebound")["version"])

    def test_generated_arcade_output_lists_grid_siege_card_snapshots_and_thumbnail(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn("games <strong>3 games</strong>", html)
        self.assertIn("Corebound", html)
        self.assertIn("Dark Factory Dispatch", html)
        self.assertIn("Void Prospector", html)
        self.assertIn('href="games/corebound/"', html)
        self.assertIn('href="games/dark-factory-dispatch/"', html)
        self.assertIn('href="games/void-prospector/"', html)
        self.assertIn('src="games/dark-factory-dispatch/assets/arcade-title-card.png"', html)
        self.assertIn("playable / v0.2.0", html)
        self.assertIn("v0.2.0 Grid Siege", html)
        self.assertIn("facility power-grid layer", html)
        self.assertIn("Reserve Ledger Audit directives", html)
        self.assertIn("blackout pressure", html)
        self.assertIn('href="games/dark-factory-dispatch/versions/0.2.0/"', html)
        self.assertIn("v0.1.0 Escalation Shift", html)
        self.assertIn("v0.0.1 Dispatch Floor", html)
        self.assertIn("Snapshots", html)
        self.assertIn('href="games/dark-factory-dispatch/versions/0.1.0/"', html)
        self.assertIn('href="games/dark-factory-dispatch/versions/0.0.1/"', html)
        self.assertIn('href="games/void-prospector/versions/0.0.1/"', html)
        self.assertNotIn("Snapshot deferred", html)

    def test_snapshot_directory_preserves_playable_static_grid_siege_release(self) -> None:
        snapshot_dir = ROOT / "games" / "dark-factory-dispatch" / "versions" / "0.2.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "dark-factory-dispatch.js").read_text(encoding="utf-8")

        self.assertIn("<title>Dark Factory Dispatch</title>", html)
        self.assertIn("dark-factory-dispatch.css", html)
        self.assertIn("dark-factory-dispatch.js", html)
        self.assertIn('id="escalation-surface"', html)
        self.assertIn('id="grid-siege-board"', html)
        self.assertIn('src="assets/arcade-title-card.png"', html)
        self.assertIn("v0.2.0 Grid Siege", script)
        self.assertIn("coolant-diversion", script)
        self.assertIn("emergency-first", script)
        self.assertIn("toggleLaneOverdrive", script)
        self.assertIn("patch-audit-relay", script)
        self.assertIn("Reserve Ledger Audit", script)
        self.assertIn("routePowerToSector", script)
        self.assertIn("isolateGridSector", script)
        self.assertIn("authorizeReserveDraw", script)
        self.assertIn("deferAuditDirective", script)
        self.assertNotIn("/versions/", script)
        self.assertFalse((snapshot_dir / "versions").exists())
        self.assertTrue((snapshot_dir / "assets" / "arcade-title-card.png").is_file())
        self.assertTrue((snapshot_dir / "assets" / "asset-manifest.json").is_file())
        self.assertRegex(game_by_slug("dark-factory-dispatch")["versions"][0]["commit"], r"^[0-9a-f]{40}$")

    def test_escalation_shift_snapshot_remains_available_after_grid_siege_release(self) -> None:
        game = game_by_slug("dark-factory-dispatch")
        snapshot_dir = ROOT / "games" / "dark-factory-dispatch" / "versions" / "0.1.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "dark-factory-dispatch.js").read_text(encoding="utf-8")

        self.assertEqual("0.1.0", game["versions"][1]["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.1.0/", game["versions"][1]["path"])
        self.assertIn("<title>Dark Factory Dispatch</title>", html)
        self.assertIn("v0.1.0 Escalation Shift", script)
        self.assertIn("coolant-diversion", script)
        self.assertNotIn("patch-audit-relay", script)
        self.assertNotIn("/versions/", script)


if __name__ == "__main__":
    unittest.main()
