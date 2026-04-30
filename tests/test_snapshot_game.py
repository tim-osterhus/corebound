import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import snapshot_game


class SnapshotGameTests(unittest.TestCase):
    def test_create_snapshot_copies_game_and_updates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            game_dir = root / "games" / "corebound"
            data_dir.mkdir()
            game_dir.mkdir(parents=True)
            (game_dir / "index.html").write_text(
                '<!doctype html><link rel="icon" href="../../favicon.png" /><a href="../../">Millrace Arcade</a>Corebound',
                encoding="utf-8",
            )
            (game_dir / "versions").mkdir()
            (game_dir / "versions" / "old.txt").write_text("do not copy", encoding="utf-8")
            manifest_path = data_dir / "games.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "games": [
                            {
                                "slug": "corebound",
                                "title": "Corebound",
                                "version": "0.2.0",
                                "status": "playable",
                                "summary": "Mine deeper.",
                                "path": "games/corebound/",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(snapshot_game, "ROOT", root), mock.patch.object(
                snapshot_game, "MANIFEST_PATH", manifest_path
            ), mock.patch.object(snapshot_game.build_arcade, "build") as build:
                entry = snapshot_game.create_snapshot(
                    slug="corebound",
                    label="Drillworks",
                    released_at="2026-04-27",
                    commit="abcdef1234567890",
                )

            snapshot_dir = root / "games" / "corebound" / "versions" / "0.2.0"
            self.assertEqual("games/corebound/versions/0.2.0/", entry["path"])
            self.assertTrue((snapshot_dir / "index.html").is_file())
            self.assertFalse((snapshot_dir / "versions").exists())
            self.assertEqual("abcdef1234567890", entry["commit"])
            build.assert_called_once()
            snapshot_html = (snapshot_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="../../../../favicon.png"', snapshot_html)
            self.assertIn('href="../../../../">Millrace Arcade', snapshot_html)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            versions = manifest["games"][0]["versions"]
            self.assertEqual("0.2.0", versions[0]["version"])
            self.assertEqual("Drillworks", versions[0]["label"])

    def test_create_snapshot_clears_matching_deferral(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            game_dir = root / "games" / "corebound"
            data_dir.mkdir()
            game_dir.mkdir(parents=True)
            (game_dir / "index.html").write_text("<!doctype html>Corebound", encoding="utf-8")
            manifest_path = data_dir / "games.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "games": [
                            {
                                "slug": "corebound",
                                "title": "Corebound",
                                "version": "0.2.0",
                                "path": "games/corebound/",
                                "snapshot": {
                                    "status": "deferred",
                                    "version": "0.2.0",
                                    "reason": "Working-tree release.",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(snapshot_game, "ROOT", root), mock.patch.object(
                snapshot_game, "MANIFEST_PATH", manifest_path
            ), mock.patch.object(snapshot_game.build_arcade, "build"):
                snapshot_game.create_snapshot(slug="corebound", commit="abcdef", rebuild_index=False)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertNotIn("snapshot", manifest["games"][0])

    def test_create_snapshot_can_omit_commit_for_working_tree_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            game_dir = root / "games" / "corebound"
            data_dir.mkdir()
            game_dir.mkdir(parents=True)
            (game_dir / "index.html").write_text("<!doctype html>Corebound", encoding="utf-8")
            manifest_path = data_dir / "games.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "games": [
                            {
                                "slug": "corebound",
                                "title": "Corebound",
                                "version": "0.3.0",
                                "path": "games/corebound/",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(snapshot_game, "ROOT", root), mock.patch.object(
                snapshot_game, "MANIFEST_PATH", manifest_path
            ), mock.patch.object(snapshot_game, "current_commit", return_value="abcdef"), mock.patch.object(
                snapshot_game.build_arcade, "build"
            ):
                entry = snapshot_game.create_snapshot(
                    slug="corebound",
                    label="Working Tree",
                    released_at="2026-04-29",
                    include_commit=False,
                )

            self.assertEqual("0.3.0", entry["version"])
            self.assertEqual("2026-04-29", entry["releasedAt"])
            self.assertNotIn("commit", entry)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertNotIn("commit", manifest["games"][0]["versions"][0])

    def test_defer_snapshot_records_no_commit_or_release_stamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            data_dir.mkdir()
            manifest_path = data_dir / "games.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "games": [
                            {
                                "slug": "corebound",
                                "title": "Corebound",
                                "version": "0.2.0",
                                "path": "games/corebound/",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(snapshot_game, "ROOT", root), mock.patch.object(
                snapshot_game, "MANIFEST_PATH", manifest_path
            ), mock.patch.object(snapshot_game.build_arcade, "build") as build:
                entry = snapshot_game.defer_snapshot(
                    slug="corebound",
                    label="Continuity",
                    summary="Working tree release.",
                    reason="Uncommitted working-tree content.",
                )

            self.assertEqual("deferred", entry["status"])
            self.assertEqual("0.2.0", entry["version"])
            self.assertEqual("Continuity", entry["label"])
            self.assertNotIn("commit", entry)
            self.assertNotIn("releasedAt", entry)
            build.assert_called_once()

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(entry, manifest["games"][0]["snapshot"])

    def test_existing_snapshot_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            game_dir = root / "games" / "corebound"
            snapshot_dir = game_dir / "versions" / "0.1.0"
            data_dir.mkdir()
            game_dir.mkdir(parents=True)
            snapshot_dir.mkdir(parents=True)
            (game_dir / "index.html").write_text("<!doctype html>Corebound", encoding="utf-8")
            (snapshot_dir / "index.html").write_text("existing", encoding="utf-8")
            manifest_path = data_dir / "games.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "games": [
                            {
                                "slug": "corebound",
                                "version": "0.1.0",
                                "path": "games/corebound/",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(snapshot_game, "ROOT", root), mock.patch.object(
                snapshot_game, "MANIFEST_PATH", manifest_path
            ):
                with self.assertRaises(ValueError):
                    snapshot_game.create_snapshot(slug="corebound", commit="abc", rebuild_index=False)


if __name__ == "__main__":
    unittest.main()
