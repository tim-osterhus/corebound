import json
import re
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "dark-factory-dispatch"
MANIFEST_PATH = GAME_DIR / "assets" / "asset-manifest.json"


def source_text(filename: str) -> str:
    return (GAME_DIR / filename).read_text(encoding="utf-8")


class DarkFactoryDispatchOperatorSurfaceTests(unittest.TestCase):
    def test_escalation_surface_hooks_and_operator_controls_are_present(self) -> None:
        html = source_text("index.html")
        css = source_text("dark-factory-dispatch.css")
        js = source_text("dark-factory-dispatch.js")

        for token in (
            'id="escalation-surface"',
            'aria-label="Campaign and Grid Siege status"',
            'id="grid-siege-board"',
            'id="queue-policy-select"',
            "Queue policy",
            "Grid Siege",
            "Production floor",
            "Queued jobs",
            "Dispatch board",
            "Improvement rack",
            "Operator log",
        ):
            self.assertIn(token, html)

        for token in (
            "campaignSurfaceState",
            "gridSurfaceState",
            "renderEscalationSurface",
            "renderGridSiege",
            'data-surface="campaign"',
            'data-surface="emergency"',
            'data-surface="progression"',
            'data-surface="choices"',
            'data-grid="sectors"',
            'data-action="overdrive"',
            'data-action="grid-route"',
            'data-action="grid-isolate"',
            'data-action="grid-reserve"',
            'data-action="audit-resolve"',
            'data-action="audit-defer"',
            "setQueuePolicy(currentState",
            "toggleLaneOverdrive(",
            "routePowerToSector(currentState",
            "isolateGridSector(currentState",
            "authorizeReserveDraw(currentState",
            "resolveAuditDirective(currentState",
            "deferAuditDirective(currentState",
        ):
            self.assertIn(token, js)

        for token in (
            ".escalation-strip",
            ".escalation-card",
            ".grid-panel",
            ".grid-siege-board",
            ".grid-sector-list",
            ".grid-sector-card",
            ".grid-directive-card",
            ".grid-actions",
            ".directive-actions",
            '.lane-card[data-overdrive="true"]',
            '.grid-sector-card[data-isolated="true"]',
            '.contract-card[data-emergency="true"]',
            '.queue-item[data-emergency="true"]',
            "@media (max-width: 720px)",
            "grid-template-areas:",
            "overflow-wrap: anywhere",
        ):
            self.assertIn(token, css)

    def test_campaign_surface_model_exposes_pressure_progression_and_choices(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/dark-factory-dispatch/dark-factory-dispatch.js");
            const first = game.createInitialState({ seed: 91, faultsEnabled: false });
            const firstSurface = game.campaignSurfaceState(first);

            let second = game.resetFactoryState(first);
            second.faults.enabled = false;
            const pendingSurface = game.campaignSurfaceState(second);
            second = game.stepFactory(second, 6);
            second = game.setQueuePolicy(second, "emergency-first");
            second = game.toggleLaneOverdrive(second, "forge-line", true);
            const activeSurface = game.campaignSurfaceState(second);

            console.log(JSON.stringify({ firstSurface, pendingSurface, activeSurface }));
            """
        )

        first = result["firstSurface"]
        pending = result["pendingSurface"]
        active = result["activeSurface"]

        self.assertEqual("v0.2.0 Grid Siege", first["release"])
        self.assertEqual(1, first["shift"])
        self.assertEqual("quiet", first["emergency"]["status"])
        self.assertIn("shift 02", first["emergency"]["detail"])
        self.assertEqual(0, first["progression"]["ledgerCount"])

        self.assertEqual(2, pending["shift"])
        self.assertEqual("pending", pending["emergency"]["status"])
        self.assertIn("arms t6", pending["emergency"]["detail"])
        self.assertEqual(1, pending["progression"]["ledgerCount"])
        self.assertIn("shift 01", pending["progression"]["latest"])

        self.assertEqual("Emergency First", active["queuePolicy"]["name"])
        self.assertEqual("active", active["emergency"]["status"])
        self.assertEqual(1, active["choices"]["queuePolicyChanges"])
        self.assertEqual(1, active["choices"]["laneOverdrives"])
        self.assertEqual(1, active["choices"]["activeOverdrives"])

    def test_grid_siege_surface_model_exposes_visible_decision_state(self) -> None:
        result = self.run_node(
            """
            const game = require("./games/dark-factory-dispatch/dark-factory-dispatch.js");
            let state = game.createInitialState({ run: 2, seed: 101, faultsEnabled: false });
            state = game.stepFactory(state, 4);
            const activeSurface = game.gridSurfaceState(state);

            state = game.routePowerToSector(state, "forge-bus", "priority");
            state = game.authorizeReserveDraw(state, "forge-bus");
            state = game.isolateGridSector(state, "assembly-bus", true);
            state = game.deferAuditDirective(state);
            const deferredSurface = game.gridSurfaceState(state);
            state = game.resolveAuditDirective(state);
            const resolvedSurface = game.gridSurfaceState(state);

            console.log(JSON.stringify({ activeSurface, deferredSurface, resolvedSurface }));
            """
        )

        active = result["activeSurface"]
        deferred = result["deferredSurface"]
        resolved = result["resolvedSurface"]

        self.assertEqual("active", active["audit"]["status"])
        self.assertEqual("Reserve Ledger Audit", active["audit"]["name"])
        self.assertEqual({"circuits": 1, "power": 1}, active["audit"]["repairCost"])
        self.assertEqual({"stability": 3}, active["audit"]["deferCost"])
        self.assertTrue(active["audit"]["queued"])
        self.assertEqual(3, len(active["sectors"]))
        self.assertIn("assembly-bus", active["sectors"][0]["connectedTo"] + active["sectors"][1]["connectedTo"])
        self.assertIn("laneName", active["sectors"][0])
        self.assertIn("powered", active["sectors"][0])

        self.assertEqual("priority", deferred["sectors"][0]["route"])
        self.assertEqual(2, deferred["reserve"]["available"])
        self.assertEqual(3, deferred["reserve"]["drawn"])
        self.assertTrue(deferred["sectors"][1]["isolated"])
        self.assertFalse(deferred["sectors"][1]["powered"])
        self.assertEqual(1, deferred["audit"]["deferrals"])
        self.assertGreater(deferred["audit"]["dueTick"], active["audit"]["dueTick"])
        self.assertEqual(1, deferred["choices"]["powerRoutes"])
        self.assertEqual(1, deferred["choices"]["reserveDraws"])
        self.assertEqual(1, deferred["choices"]["sectorIsolations"])

        self.assertEqual("complete", resolved["audit"]["status"])
        self.assertEqual(1, resolved["audit"]["completed"])
        self.assertEqual(1, resolved["choices"]["auditRepairs"])

    def test_grid_siege_layout_contract_uses_named_areas_and_narrow_stacking(self) -> None:
        css = source_text("dark-factory-dispatch.css")

        for token in (
            '"lanes grid grid"',
            '"controls controls log"',
            '"lanes lanes"',
            '"grid grid"',
            '"controls log"',
            '"lanes"',
            '"grid"',
            ".grid-summary,\n  .grid-sector-meta",
            ".grid-actions,\n  .directive-actions",
        ):
            self.assertIn(token, css)

        self.assertNotIn("overflow-x: scroll", css)

    def test_escalation_surface_does_not_add_stale_raster_asset_references(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_paths = {
            asset["path"].removeprefix("games/dark-factory-dispatch/")
            for asset in manifest["assets"]
        }
        combined = "\n".join(
            source_text(filename)
            for filename in (
                "index.html",
                "dark-factory-dispatch.css",
                "dark-factory-dispatch.js",
            )
        )

        for reference in re.findall(r'assets/[^"\'\)\s]+\.png', combined):
            self.assertIn(reference, manifest_paths, reference)

        self.assertNotIn("job-stabilize-grid.png", combined)
        self.assertNotIn('"stabilize-grid": "assets/', combined)

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
