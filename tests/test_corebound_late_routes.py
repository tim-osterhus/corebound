import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "corebound"


class CoreboundLateRouteTests(unittest.TestCase):
    def test_hud_exposes_late_route_choice_surface(self) -> None:
        html = (GAME_DIR / "index.html").read_text(encoding="utf-8")

        for surface_id in (
            "route-status",
            "route-progress",
            "route-list",
        ):
            self.assertIn(surface_id, html)
        self.assertIn("Late Route", html)
        self.assertIn("Choose a late-run line before launch", html)

    def test_late_run_content_and_route_choices_are_data_driven(self) -> None:
        data = (GAME_DIR / "corebound-data.js").read_text(encoding="utf-8")

        for content_id in (
            "choir trench",
            "choirSlate",
            "anchorRib",
            "echoPearl",
            "relayCore",
            "gravityShear",
            "voidChoir",
        ):
            self.assertIn(content_id, data)
        self.assertIn("depth: 138", data)
        self.assertIn("routePlans", data)
        for route_id in ("standardLine", "thermalSpiral", "ledgerSpur"):
            self.assertIn(route_id, data)
        self.assertIn("requires: { charters: 1 }", data)
        self.assertIn('requiresCharter: "ledgerTitheCharter"', data)
        self.assertIn("effects: { scanRange: 1, charterDrillHeat: 1, valueMultiplier: 0.08 }", data)
        self.assertIn("effects: { beaconCharges: 1, returnEnergyPenalty: 0.08, valueMultiplier: 0.12 }", data)
        self.assertIn("archiveFragments: { voidChoir: 1 }", data)

    def test_anchor_recall_is_charter_rewarded_extraction_choice(self) -> None:
        data = (GAME_DIR / "corebound-data.js").read_text(encoding="utf-8")
        script = (GAME_DIR / "corebound.js").read_text(encoding="utf-8")

        self.assertIn("anchorCharges: 0", data)
        self.assertIn("relayEffects: { scanRange: 1, anchorCharges: 1 }", data)
        self.assertIn("anchorRecall", data)
        self.assertIn('chargesStat: "anchorCharges"', data)
        self.assertIn("effects: { anchorCharges: 1, beaconReturnEfficiency: 0.06, archiveSignal: 1 }", data)

        for behavior in (
            "triggerAnchorRecall",
            "state.runRouteId = state.activeRouteId",
            "state.routeProgress[state.runRouteId] = 0",
            "routePlanUnlocked",
            "selectRoutePlan",
            "updateRouteProgress",
            "completeRunRoute",
            "renderRoutePanel",
        ):
            self.assertIn(behavior, script)
        self.assertIn("applyStatEffects(stats, activeRoute.effects)", script)
        self.assertIn("state.routeCompletions[route.id]", script)
        self.assertIn('button.addEventListener("click", () => selectRoutePlan(entry.id))', script)
        self.assertIn('} else if (utility.id === "anchorRecall") {', script)
        self.assertIn("returnToSurface(`Anchor recall hauled the rig from ${depth} m with ${cargoText}.`)", script)


if __name__ == "__main__":
    unittest.main()
