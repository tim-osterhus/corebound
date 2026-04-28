$imagegen

You are creating browser-game visual assets for a Millrace task.

Use Codex built-in image generation/editing only. Do not use OPENAI_API_KEY, the OpenAI SDK, the Images API, or any API-key fallback. Do not read or print Codex credential files.

Mode: generate
Working directory: /mnt/f/_evolve/millrace-games/auto-games
Final asset destination directory: /mnt/f/_evolve/millrace-games/auto-games/games/corebound/assets
Manifest path to write: /mnt/f/_evolve/millrace-games/auto-games/games/corebound/assets/asset-manifest.json
Reference images attached or provided:
- none

Asset brief:
Create an original Corebound bitmap asset pack for a static browser mining game with a restrained mono-first, operator-grade, diagrammatic industrial style. Use teal as a precise signal accent only. Do not copy Motherload or any commercial game art.

Create final project-consumed PNG assets in these exact files under the final asset destination directory:
- rig/mantis-rig-motion-strip.png: transparent sprite strip, 4 horizontal frames, 320x80 total, 80x80 per frame. A compact side-view mining pod named Mantis-01 with drill, treads/skids, antenna mast, and subtle per-frame engine/strut motion. No text.
- surface/surface-facilities-panel.png: 640x160 PNG scene plate showing a square-framed surface base with refinery, rig bay, assay desk, survey relay, and launch gantry. No text labels.
- surface/launch-shaft-context.png: 320x320 PNG showing a clean vertical shaft collar descending from the base into strata, readable as launch context. No text.
- terrain/loam-gritstone-tile.png: 128x128 tile texture for upper loam/gritstone strata, subdued dark mineral plates with subtle grid-readable edges.
- terrain/basalt-core-tile.png: 128x128 tile texture for deep basalt/core rind strata, darker and denser, with faint teal diagnostic seams.
- terrain/pressure-glass-tile.png: 128x128 tile texture for pressure glass/choir slate strata, smoky dark glass with restrained luminous fracture lines.
- readables/ore-hazard-atlas.png: 384x128 transparent atlas with six 64x64 cells: copper seed, saltglass, cobalt thread, heat fissure, gas vent, magnetic bloom. Each cell centered, no text.
- hud/hud-icon-atlas.png: 320x64 transparent atlas with five 64x64 cells: hull, energy, heat, cargo, depth. No text.
- upgrades/upgrade-research-atlas.png: 512x128 transparent atlas with eight 64x64 cells: drill, cargo, scanner, hazard sheath, refinery loop, anchor recall, coolant dump, archive relay. No text.

Style constraints for all files: original art, industrial, slightly alien, square-framed silhouettes, high readability at small game scale, dark graphite/steel base colors, teal accents only for sensor/light signals, no words, no logo marks, no watermarks.

After generating the assets, write the manifest JSON at the requested manifest path with schema_version 1, status complete, mode generate, workdir, and an assets array. Each asset entry must include id, path relative to the workdir, role, description, width, height, intended_use, and notes. Use stable ids: rig.mantis_motion_strip, surface.facilities_panel, surface.launch_shaft_context, terrain.loam_gritstone_tile, terrain.basalt_core_tile, terrain.pressure_glass_tile, readables.ore_hazard_atlas, hud.icon_atlas, upgrades.research_atlas.

Requirements:
- Create original assets only; do not copy protected game art, characters, names, logos, maps, or exact presentation.
- Save every final project-consumed asset under the final asset destination directory.
- Keep UI text, labels, scores, and controls out of raster assets unless the brief explicitly asks for baked-in text.
- For edits, preserve the source non-destructively and write a new output file.
- If transparency is needed, make the final file a PNG or WebP with usable alpha, or clearly report why that was not possible.
- Prefer stable, descriptive lowercase filenames.
- After generation or editing, write the manifest JSON exactly at the manifest path.

Manifest schema:
{
  "schema_version": 1,
  "status": "complete | blocked",
  "mode": "generate",
  "workdir": "/mnt/f/_evolve/millrace-games/auto-games",
  "assets": [
    {
      "path": "absolute or workdir-relative path to an asset",
      "role": "sprite | sprite-strip | icon | background | texture | concept | other",
      "description": "short asset description",
      "width": null,
      "height": null,
      "notes": "generation or editing notes"
    }
  ],
  "notes": "short summary, or blocker reason when status is blocked"
}

Finish with a concise summary of files created and any checks the caller should run.
