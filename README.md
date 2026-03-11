# auto-games

`auto-games` is the local games repo that publishes to the GitHub repo `auto-games`.

This repo publishes the versioned browser-game arcade behind `game.millrace.ai`.

- `game.millrace.ai` is a generated arcade index page.
- each published title is described in `data/games.json`
- public releases start lean and grow through visible version bumps

## Source Of Truth

The discoverable games list lives in `data/games.json`.

`scripts/build_arcade.py` reads that manifest and generates:

- `index.html`
- `assets/site.css`
- one static page per game slug, such as `corebound/index.html`

## Update Flow

1. Edit `data/games.json`.
2. Run:

```bash
python3 scripts/build_arcade.py
```

3. Verify the generated output:

```bash
python3 -m unittest tests.test_build_arcade
```

## Current Public State

The first published title is `corebound`, live as version `0.0.1` on the public release track.
