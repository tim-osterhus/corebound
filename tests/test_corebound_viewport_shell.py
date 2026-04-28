import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "games" / "corebound"


class CoreboundViewportShellTests(unittest.TestCase):
    def test_viewport_contains_compact_hud_surface_dock_and_focusable_canvas(self) -> None:
        html = (GAME_DIR / "index.html").read_text(encoding="utf-8")

        viewport_start = html.index('<div class="viewport-frame">')
        menu_start = html.index('<section class="help-surface menu-surface"')

        for contract in (
            'tabindex="0"',
            'class="hud in-game-hud"',
            'id="service-context"',
            'id="warning-readout"',
            'class="surface-panel surface-dock"',
            'aria-label="Surface services"',
            'class="control-pad"',
        ):
            self.assertIn(contract, html)
            self.assertGreater(html.index(contract), viewport_start)

        self.assertGreater(menu_start, viewport_start)
        self.assertLess(html.index('class="surface-panel surface-dock"'), menu_start)

    def test_secondary_systems_live_in_the_menu_surface(self) -> None:
        html = (GAME_DIR / "index.html").read_text(encoding="utf-8")
        menu_start = html.index('<section class="help-surface menu-surface"')

        for surface in (
            'class="resource-ledger menu-block"',
            'class="surface-lists menu-block"',
            'class="contract-panel menu-block"',
            'class="charter-panel menu-block"',
            'class="route-panel menu-block"',
            'class="archive-panel menu-block"',
            'class="facility-panel menu-block"',
            'id="upgrade-list"',
            'id="research-list"',
            'id="contract-list"',
            'id="charter-list"',
            'id="route-list"',
            'id="archive-list"',
            'id="utility-list"',
        ):
            self.assertIn(surface, html)
            self.assertGreater(html.index(surface), menu_start)

    def test_viewport_css_prevents_document_scroll_and_uses_internal_surfaces(self) -> None:
        css = (GAME_DIR / "corebound.css").read_text(encoding="utf-8")

        for rule in (
            "overflow: hidden;",
            "height: 100svh;",
            ".viewport-frame",
            ".hud-topline",
            ".in-game-hud #objective-list",
            ".surface-dock",
            ".surface-dock-away",
            ".help-surface",
            "max-height: min(72vh, 640px);",
            "grid-template-columns: minmax(0, 1fr) 42px;",
        ):
            self.assertIn(rule, css)

    def test_menu_toggle_and_focus_behavior_are_keyboard_safe(self) -> None:
        script = (GAME_DIR / "corebound.js").read_text(encoding="utf-8")

        for behavior in (
            "serviceContextLabel",
            "warningLabel",
            "focusGameSurface",
            "isHelpOpen",
            "clearHeldInput();",
            "setHelpOpen(open, restoreFocus)",
            'event.key === "Escape"',
            "setHelpOpen(hud.help.surface.hidden, true)",
            'hud.help.toggle.setAttribute("aria-expanded", open ? "true" : "false")',
            'hud.surfacePanel.classList.toggle("surface-dock-away", !dockOpen)',
            "const aspectCols = Math.ceil((canvas.width / Math.max(1, canvas.height)) * rows)",
            "cols: clamp(Math.max(minimumCols, aspectCols), minimumCols, DATA.world.width)",
        ):
            self.assertIn(behavior, script)


if __name__ == "__main__":
    unittest.main()
