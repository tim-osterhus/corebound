import json
import re
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "iron-lantern-descent"
MANIFEST_PATH = GAME_DIR / "assets" / "asset-manifest.json"


def source_text(filename: str) -> str:
    return (GAME_DIR / filename).read_text(encoding="utf-8")


class IronLanternDescentFaultlineSurfaceTests(unittest.TestCase):
    def test_faultline_survey_dom_exposes_readouts_controls_and_logs(self) -> None:
        html = source_text("index.html")
        css = source_text("iron-lantern-descent.css")

        for token in (
            "v0.1.0 faultline survey",
            "survey-readout",
            "stability-readout",
            "tremor-readout",
            "map-readout",
            "survey-site-list",
            "event-log",
            "stake-action",
            "brace-action",
            "chart-action",
            "cache-action",
        ):
            self.assertIn(token, html)

        for token in (
            ".survey-list",
            ".survey-line",
            ".survey-meta",
            ".event-log",
            'li[data-window="tremor"]',
            'li[data-status="success"]',
            "overflow-wrap: anywhere",
            "grid-template-columns: repeat(2, minmax(0, 1fr))",
        ):
            self.assertIn(token, css)

        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)

    def test_faultline_surface_hooks_render_live_survey_state(self) -> None:
        script = source_text("iron-lantern-descent.js")

        for token in (
            "formatSurveyWindow",
            "activeSurveySite",
            "surveyRequirementText",
            'dom["survey-readout"].textContent',
            'dom["stability-readout"].textContent',
            'dom["tremor-readout"].textContent',
            'dom["map-readout"].textContent',
            'dom["survey-site-list"].replaceChildren',
            'dom["event-log"].replaceChildren',
            'dom["stake-action"].addEventListener',
            'dom["brace-action"].addEventListener',
            'dom["chart-action"].addEventListener',
            'dom["cache-action"].addEventListener',
            "plantSurveyStake(currentState)",
            "braceSurveySite(currentState)",
            "chartFaultSurvey(currentState)",
            "activateAirCache(currentState)",
        ):
            self.assertIn(token, script)

    def test_faultline_visuals_are_procedural_and_manifest_stays_truthful(self) -> None:
        script = source_text("iron-lantern-descent.js")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_paths = {asset["path"].removeprefix("games/iron-lantern-descent/") for asset in manifest["assets"]}

        for token in (
            "createSurveySiteMesh",
            "updateSurveyMeshes",
            "surveyMeshes",
            "new THREE.BufferGeometry().setFromPoints",
            "new THREE.TorusGeometry",
            "userData.role = \"fault-seam\"",
            "userData.role = \"survey-stake\"",
            "userData.role = \"brace-frame\"",
            "userData.role = \"air-cache\"",
            "userData.role = \"map-plate\"",
            "0x4bd6c0",
            "0xd46857",
            "0xc9a653",
        ):
            self.assertIn(token, script)

        self.assertEqual("complete", manifest["status"])
        self.assertEqual(
            {
                "assets/lantern-anchor.png",
                "assets/mineral-vein-material.png",
                "assets/drill-tool.png",
                "assets/oxygen-light-icons.png",
                "assets/arcade-title-card.png",
            },
            manifest_paths,
        )
        for stale_raster in ("fault", "survey", "brace", "cache", "map-plate", "tremor"):
            self.assertNotRegex(script, rf'assets/[^"\'\)\s]*{re.escape(stale_raster)}[^"\'\)\s]*\.png')

    def test_surface_controls_change_survey_state_and_route_pressure(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/iron-lantern-descent/iron-lantern-descent.js");
            let state = game.createInitialState({ seed: 83 });
            state.player.position = { x: 17, y: 1.6, z: -31 };
            state.elapsed = 40;
            state = game.syncDerivedState(state);
            const before = {
              stability: state.routeStability.stability,
              routeConfidence: state.route.returnConfidence,
              oxygen: state.oxygen.current,
              lastLog: state.log[0].message,
            };
            state = game.plantSurveyStake(state, "survey-cinder-rib");
            const staked = {
              stability: state.routeStability.stability,
              routeConfidence: state.route.returnConfidence,
              stakes: state.survey.stakes,
              lastLog: state.log[0].message,
            };
            state = game.chartFaultSurvey(state, "survey-cinder-rib");
            const charted = {
              chartState: state.surveySites[0].chartState,
              mapProgress: state.survey.mapProgress,
              surveyValue: state.survey.value,
              oxygen: state.oxygen.current,
              lastLog: state.log[0].message,
            };

            console.log(JSON.stringify({ before, staked, charted }));
            """
        )

        self.assertGreater(result["staked"]["stability"], result["before"]["stability"])
        self.assertGreater(result["staked"]["routeConfidence"], result["before"]["routeConfidence"])
        self.assertEqual(1, result["staked"]["stakes"])
        self.assertIn("survey stake planted", result["staked"]["lastLog"])
        self.assertEqual("partial", result["charted"]["chartState"])
        self.assertEqual(0.5, result["charted"]["mapProgress"])
        self.assertEqual(18, result["charted"]["surveyValue"])
        self.assertLess(result["charted"]["oxygen"], result["before"]["oxygen"])
        self.assertIn("chart partial", result["charted"]["lastLog"])

    def run_node(self, script: str) -> dict:
        completed = subprocess.run(
            ["node", "-e", textwrap.dedent(script)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
