$imagegen

You are creating browser-game visual assets for a Millrace task.

Use Codex built-in image generation/editing only. Do not use OPENAI_API_KEY, the OpenAI SDK, the Images API, or any API-key fallback. Do not read or print Codex credential files.

Mode: generate
Working directory: /mnt/f/_evolve/millrace-games/auto-games
Final asset destination directory: /mnt/f/_evolve/millrace-games/auto-games/games/iron-lantern-descent/assets
Manifest path to write: /mnt/f/_evolve/millrace-games/auto-games/_visual-check/iron-lantern-descent-assets/asset-request-manifest.json
Reference images attached or provided:
- none

Asset brief:
Create a compact original Iron Lantern Descent browser-game raster asset pack in the Millrace visual direction: mono-first, operator-grade, diagrammatic, restrained, square-framed, lightly luminous, with teal used as precise signal and warm lantern light as mechanical readability. Final project assets must be PNG files under games/iron-lantern-descent/assets with stable lowercase names and no baked UI text, logos, watermarks, remote references, protected characters, or CSS-only placeholders. Required files and roles: lantern-anchor.png, 256x256 transparent PNG, an iron lantern anchor cutout/model treatment with tripod clamp, cage, warm amber core, and small teal alignment signal for in-world route anchors; mineral-vein-material.png, 512x512 opaque square cave crystal/mineral material with charcoal rock, faceted mineral seams, teal crystal interference glow, and subtle amber ore glints for sample nodes and cave material; drill-tool.png, 256x256 transparent PNG, compact handheld drill/sample tool cutout with steel body, bit, amber work lamp, and teal status stripe for HUD/tool feedback; oxygen-light-icons.png, 384x128 transparent PNG icon atlas with three 128x128 cells for oxygen tank, lantern/light, and scanner/route pulse icons, no text, consistent line weight; arcade-title-card.png, 800x450 opaque PNG, title-card art of a close-third-person cave descent from the iron lift with route lanterns, mineral veins, drill cues, and restrained teal/amber signals, no readable text. Write manifest JSON with one asset entry per file, include width and height, intended use, role, and notes.

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
