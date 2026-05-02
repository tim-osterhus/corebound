import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "dark-factory-dispatch"
MANIFEST_PATH = GAME_DIR / "assets" / "asset-manifest.json"


def source_text(filename: str) -> str:
    return (GAME_DIR / filename).read_text(encoding="utf-8")


def manifest_short_paths() -> set[str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        asset["path"].removeprefix("games/dark-factory-dispatch/")
        for asset in manifest["assets"]
    }


class DarkFactoryDispatchAssetIntegrationTests(unittest.TestCase):
    def test_static_asset_references_are_project_local_manifest_assets(self) -> None:
        paths = manifest_short_paths()
        files = {
            "index.html": source_text("index.html"),
            "dark-factory-dispatch.css": source_text("dark-factory-dispatch.css"),
            "dark-factory-dispatch.js": source_text("dark-factory-dispatch.js"),
        }

        for filename, text in files.items():
            for reference in re.findall(r'assets/[^"\'\)\s]+\.png', text):
                self.assertIn(reference, paths, f"{filename} references {reference}")
                self.assertNotIn("://", reference)
                self.assertFalse(Path(reference).is_absolute())

        self.assertIn("assets/arcade-title-card.png", paths)
        self.assertIn('sourceManifest: "assets/asset-manifest.json"', files["dark-factory-dispatch.js"])
        self.assertIn('data-breach-countermeasure="${jobType.breachCountermeasure ? "true" : "false"}"', files["dark-factory-dispatch.js"])
        self.assertIn('data-freight-inspection="${jobType.freightInspection ? "true" : "false"}"', files["dark-factory-dispatch.js"])
        self.assertIn('data-sabotage-sweep="${jobType.sabotageSweep ? "true" : "false"}"', files["dark-factory-dispatch.js"])
        self.assertIn('id="freight-lockdown-board"', files["index.html"])
        self.assertIn('id="rail-sabotage-board"', files["index.html"])
        self.assertIn('id="crisis-arbitration-board"', files["index.html"])
        self.assertIn('data-action="crisis-evidence"', files["dark-factory-dispatch.js"])
        self.assertIn('data-action="crisis-rule"', files["dark-factory-dispatch.js"])
        self.assertNotIn("assets/job-compile-countermeasures.png", files["dark-factory-dispatch.js"])
        self.assertNotIn("assets/job-inspect-cargo-seals.png", files["dark-factory-dispatch.js"])
        self.assertNotIn("assets/freight-", "\n".join(files.values()))
        self.assertNotIn("assets/sabotage-", "\n".join(files.values()))
        self.assertNotIn("assets/rail-", "\n".join(files.values()))
        self.assertNotIn("assets/crisis-", "\n".join(files.values()))
        self.assertNotIn("assets/arbitration-", "\n".join(files.values()))
        self.assertNotIn("assets/docket-", "\n".join(files.values()))

    def test_lane_job_and_fault_renderers_use_generated_icon_paths(self) -> None:
        script = source_text("dark-factory-dispatch.js")
        css = source_text("dark-factory-dispatch.css")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        for token in (
            "ASSET_PATHS",
            "PROCEDURAL_FEEDBACK_ASSETS",
            "factoryFeedbackState",
            "laneFeedbackState",
            "resourceFeedbackState",
            "jobFeedbackState",
            "upgradeFeedbackState",
            "shiftSummaryFeedbackState",
            "iconMarkup",
            '"forge-line": "assets/lane-forge-line.png"',
            '"assembler-bay": "assets/lane-assembler-bay.png"',
            '"clean-room": "assets/lane-clean-room.png"',
            '"smelt-circuits": "assets/job-smelt-circuits.png"',
            '"print-modules": "assets/job-print-modules.png"',
            '"assemble-drones": "assets/job-assemble-drones.png"',
            '"weave-defenses": "assets/job-weave-defenses.png"',
            '"material-jam": "assets/fault-material-jam.png"',
            '"logic-drift": "assets/fault-logic-drift.png"',
            "fault-readout",
            'data-visual-hook="lane-feedback"',
            'data-feedback="${feedback.feedback}"',
            'data-output="${feedback.outputResource || "none"}"',
            'data-shortage="${feedback.shortage ? "true" : "false"}"',
            'data-procedural-asset="${summaryFeedback.proceduralAsset}"',
        ):
            self.assertIn(token, script)

        for token in (
            ".asset-icon",
            ".lane-icon",
            ".fault-icon",
            '.fault-readout[data-active="true"]',
            ".lane-board::before",
            ".resource-glyph[data-resource-icon",
            '.lane-card[data-feedback="production"]',
            '.lane-card[data-feedback="jam"]',
            '.lane-card[data-feedback="recovery"]',
            ".output-token[data-active=\"true\"]",
            ".overdrive-glow[data-active=\"true\"]",
            ".feedback-sparks[data-active=\"true\"]",
            ".incident-marker[data-active=\"true\"]",
            ".upgrade-icon[data-upgrade-family",
            '.shift-summary-card[data-feedback="summary-open"]',
        ):
            self.assertIn(token, css)

        fallback_ids = {fallback["id"] for fallback in manifest["procedural_fallbacks"]}
        self.assertEqual(
            {
                "factory-floor-board",
                "resource-signal-glyphs",
                "output-delivery-token",
                "shortage-marker",
                "overdrive-heat-glow",
                "jam-sparks",
                "sabotage-incident-marker",
                "shift-summary-header",
                "upgrade-family-icons",
            },
            fallback_ids,
        )
        for fallback in manifest["procedural_fallbacks"]:
            self.assertTrue(fallback["hook"])
            self.assertTrue(fallback["reason"])
            self.assertTrue(fallback["implementation"].startswith("css:"))


if __name__ == "__main__":
    unittest.main()
