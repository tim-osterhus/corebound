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
    def test_manifest_adds_truthful_dark_factory_dispatch_freight_lockdown_release(self) -> None:
        game = game_by_slug("dark-factory-dispatch")

        self.assertEqual("Dark Factory Dispatch", game["title"])
        self.assertEqual("0.4.0", game["version"])
        self.assertEqual("playable", game["status"])
        self.assertEqual("games/dark-factory-dispatch/", game["path"])
        self.assertEqual("games/dark-factory-dispatch/assets/arcade-title-card.png", game["thumbnail"])
        self.assertIn("Freight Lockdown shifts", game["summary"])
        self.assertIn("outbound freight manifests", game["summary"])
        self.assertIn("dock loading windows", game["summary"])
        self.assertIn("staged cargo", game["summary"])
        self.assertIn("carrier seals", game["summary"])
        self.assertIn("launch clearance", game["summary"])
        self.assertIn("route-security escorts", game["summary"])
        self.assertIn("reroute decisions", game["summary"])
        self.assertIn("cargo-integrity outcomes", game["summary"])
        self.assertIn("Signal Breach intrusion", game["summary"])
        self.assertIn("Grid Siege power routing", game["summary"])
        self.assertIn("audit relay directives", game["summary"])
        self.assertIn("emergency coolant-diversion orders", game["summary"])
        self.assertIn("lane overdrive calls", game["summary"])
        self.assertEqual("v0.4.0 Freight Lockdown", game["release"]["label"])
        self.assertIn("outbound logistics pressure", game["release"]["copy"])
        self.assertIn("stage cargo into freight manifests", game["release"]["copy"])
        self.assertIn("inspect dock seals", game["release"]["copy"])
        self.assertIn("assign escort drones or defense screens", game["release"]["copy"])
        self.assertIn("spend reserve clearance", game["release"]["copy"])
        self.assertIn("reroute contaminated sectors", game["release"]["copy"])
        self.assertIn("hold launch windows", game["release"]["copy"])
        self.assertIn("seal carriers", game["release"]["copy"])
        self.assertIn("full, partial, or failed cargo outcomes", game["release"]["copy"])
        self.assertIn("Grid Siege", game["release"]["copy"])

        self.assertNotIn("snapshot", game)
        versions = game["versions"]
        self.assertEqual(["0.4.0", "0.3.0", "0.2.0", "0.1.0", "0.0.1"], [entry["version"] for entry in versions])

        current_snapshot = versions[0]
        self.assertEqual("games/dark-factory-dispatch/versions/0.4.0/", current_snapshot["path"])
        self.assertEqual("2026-04-29", current_snapshot["releasedAt"])
        self.assertEqual("v0.4.0 Freight Lockdown", current_snapshot["label"])
        self.assertIn("Outbound freight manifests", current_snapshot["summary"])
        self.assertIn("dock loading windows", current_snapshot["summary"])
        self.assertIn("cargo staging", current_snapshot["summary"])
        self.assertIn("carrier seals", current_snapshot["summary"])
        self.assertIn("route-security escorts", current_snapshot["summary"])
        self.assertIn("reserve launch clearance", current_snapshot["summary"])
        self.assertIn("reroutes around contaminated sectors", current_snapshot["summary"])
        self.assertIn("cargo-integrity outcomes", current_snapshot["summary"])
        self.assertIn("Signal Breach release", current_snapshot["summary"])
        self.assertNotIn("commit", current_snapshot)

        signal_snapshot = versions[1]
        self.assertEqual("0.3.0", signal_snapshot["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.3.0/", signal_snapshot["path"])
        self.assertEqual("v0.3.0 Signal Breach", signal_snapshot["label"])

        grid_snapshot = versions[2]
        self.assertEqual("0.2.0", grid_snapshot["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.2.0/", grid_snapshot["path"])
        self.assertEqual("v0.2.0 Grid Siege", grid_snapshot["label"])
        self.assertRegex(grid_snapshot["commit"], r"^[0-9a-f]{40}$")

        escalation_snapshot = versions[3]
        self.assertEqual("0.1.0", escalation_snapshot["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.1.0/", escalation_snapshot["path"])
        self.assertEqual("v0.1.0 Escalation Shift", escalation_snapshot["label"])

        first_snapshot = versions[4]
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

    def test_generated_arcade_output_lists_freight_lockdown_card_snapshots_and_thumbnail(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn("games <strong>3 games</strong>", html)
        self.assertIn("Corebound", html)
        self.assertIn("Dark Factory Dispatch", html)
        self.assertIn("Void Prospector", html)
        self.assertIn('href="games/corebound/"', html)
        self.assertIn('href="games/dark-factory-dispatch/"', html)
        self.assertIn('href="games/void-prospector/"', html)
        self.assertIn('src="games/dark-factory-dispatch/assets/arcade-title-card.png"', html)
        self.assertIn("playable / v0.4.0", html)
        self.assertIn("v0.4.0 Freight Lockdown", html)
        self.assertIn("outbound logistics pressure", html)
        self.assertIn("stage cargo into freight manifests", html)
        self.assertIn("inspect dock seals", html)
        self.assertIn("assign escort drones or defense screens", html)
        self.assertIn("spend reserve clearance", html)
        self.assertIn("reroute contaminated sectors", html)
        self.assertIn("full, partial, or failed cargo outcomes", html)
        self.assertIn('href="games/dark-factory-dispatch/versions/0.4.0/"', html)
        self.assertIn('href="games/dark-factory-dispatch/versions/0.3.0/"', html)
        self.assertIn("v0.3.0 Signal Breach", html)
        self.assertIn("v0.2.0 Grid Siege", html)
        self.assertIn("v0.1.0 Escalation Shift", html)
        self.assertIn("v0.0.1 Dispatch Floor", html)
        self.assertIn("Snapshots", html)
        self.assertIn('href="games/dark-factory-dispatch/versions/0.2.0/"', html)
        self.assertIn('href="games/dark-factory-dispatch/versions/0.1.0/"', html)
        self.assertIn('href="games/dark-factory-dispatch/versions/0.0.1/"', html)
        self.assertIn('href="games/void-prospector/versions/0.0.1/"', html)
        self.assertNotIn("Snapshot deferred", html)

    def test_snapshot_directory_preserves_playable_static_freight_lockdown_release(self) -> None:
        snapshot_dir = ROOT / "games" / "dark-factory-dispatch" / "versions" / "0.4.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "dark-factory-dispatch.js").read_text(encoding="utf-8")

        self.assertIn("<title>Dark Factory Dispatch</title>", html)
        self.assertIn("dark-factory-dispatch.css", html)
        self.assertIn("dark-factory-dispatch.js", html)
        self.assertIn('id="escalation-surface"', html)
        self.assertIn('id="grid-siege-board"', html)
        self.assertIn('id="freight-lockdown-board"', html)
        self.assertIn('src="assets/arcade-title-card.png"', html)
        self.assertIn("v0.4.0 Freight Lockdown", script)
        self.assertIn("freightLockdown", script)
        self.assertIn("ashline-spare-crates", script)
        self.assertIn("blackout-relay-carrier", script)
        self.assertIn("inspect-cargo-seals", script)
        self.assertIn("stageFreightCargo", script)
        self.assertIn("holdFreightManifest", script)
        self.assertIn("assignFreightRouteSecurity", script)
        self.assertIn("authorizeFreightLaunchClearance", script)
        self.assertIn("rerouteFreightManifest", script)
        self.assertIn("sealFreightCarrier", script)
        self.assertIn("launchFreightManifest", script)
        self.assertIn("freightSurfaceState", script)
        self.assertIn("compile-countermeasures", script)
        self.assertIn("breachSurfaceState", script)
        self.assertIn("patch-audit-relay", script)
        self.assertIn("Reserve Ledger Audit", script)
        self.assertNotIn("/versions/", script)
        self.assertFalse((snapshot_dir / "versions").exists())
        self.assertTrue((snapshot_dir / "assets" / "arcade-title-card.png").is_file())
        self.assertTrue((snapshot_dir / "assets" / "asset-manifest.json").is_file())
        self.assertNotIn("commit", game_by_slug("dark-factory-dispatch")["versions"][0])

    def test_signal_breach_snapshot_remains_available_after_freight_lockdown_release(self) -> None:
        game = game_by_slug("dark-factory-dispatch")
        snapshot_dir = ROOT / "games" / "dark-factory-dispatch" / "versions" / "0.3.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "dark-factory-dispatch.js").read_text(encoding="utf-8")

        self.assertEqual("0.3.0", game["versions"][1]["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.3.0/", game["versions"][1]["path"])
        self.assertIn("<title>Dark Factory Dispatch</title>", html)
        self.assertIn("v0.3.0 Signal Breach", script)
        self.assertIn("compile-countermeasures", script)
        self.assertIn("breachSurfaceState", script)
        self.assertIn("cleanseCompromisedQueueEntry", script)
        self.assertIn("quarantineBreachLane", script)
        self.assertNotIn("v0.4.0 Freight Lockdown", script)
        self.assertNotIn("stageFreightCargo", script)
        self.assertNotIn("freightSurfaceState", script)
        self.assertNotIn("/versions/", script)

    def test_grid_siege_snapshot_remains_available_after_signal_breach_release(self) -> None:
        game = game_by_slug("dark-factory-dispatch")
        snapshot_dir = ROOT / "games" / "dark-factory-dispatch" / "versions" / "0.2.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "dark-factory-dispatch.js").read_text(encoding="utf-8")

        self.assertEqual("0.2.0", game["versions"][2]["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.2.0/", game["versions"][2]["path"])
        self.assertIn("<title>Dark Factory Dispatch</title>", html)
        self.assertIn("v0.2.0 Grid Siege", script)
        self.assertIn("patch-audit-relay", script)
        self.assertIn("Reserve Ledger Audit", script)
        self.assertNotIn("v0.3.0 Signal Breach", script)
        self.assertNotIn("compile-countermeasures", script)
        self.assertNotIn("stageFreightCargo", script)
        self.assertNotIn("/versions/", script)

    def test_escalation_shift_snapshot_remains_available_after_grid_siege_release(self) -> None:
        game = game_by_slug("dark-factory-dispatch")
        snapshot_dir = ROOT / "games" / "dark-factory-dispatch" / "versions" / "0.1.0"
        html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
        script = (snapshot_dir / "dark-factory-dispatch.js").read_text(encoding="utf-8")

        self.assertEqual("0.1.0", game["versions"][3]["version"])
        self.assertEqual("games/dark-factory-dispatch/versions/0.1.0/", game["versions"][3]["path"])
        self.assertIn("<title>Dark Factory Dispatch</title>", html)
        self.assertIn("v0.1.0 Escalation Shift", script)
        self.assertIn("coolant-diversion", script)
        self.assertNotIn("patch-audit-relay", script)
        self.assertNotIn("stageFreightCargo", script)
        self.assertNotIn("/versions/", script)


if __name__ == "__main__":
    unittest.main()
