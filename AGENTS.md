# AGENTS.md — comfyui-explicite-prompt-generator

A prompt generator for ComfyUI that builds coherent, seed-reproducible adult **women aged 24–50** from dropdown menus, at every wardrobe level from clothed to fully nude, with optional explicit-action sentences. A constraint engine prevents clashing traits. Zero dependencies, fully offline — no LLM, no API keys. **This is a rework of Identity Forge (v1.1.0 lineage) at v2.0.0**: the female-first rebrand, the wardrobe ladder, the narrowed age band, and the removal of the four preset layer nodes. Built on ComfyUI V3 API (`comfy_api.latest`).

**Docs: `docs/architecture.md` (deep reference — read it before engine/data changes)**

## Current state

_Last verified: 2026-08-31 (2.0.0)_

- **Status:** in active development, released at v2.0.0 (`pyproject.toml`). **CI (`.github/workflows/ci.yml`) is the gate that matters here; the Comfy-Registry publish workflow (`.github/workflows/publish_action.yml`) may also fire on version bumps.**
- **Works (v2.0.0 rework):**
  - **Wardrobe ladder** — `wardrobe_level` control: `Lingerie` (widget default — it's a nude-prompt generator) / `Clothed` / `Swimwear` / `Topless` / `Fully nude`. Non-clothed tiers replace the outfit fields with tier-specific pools (`swimwear_style`, `lingerie_style` + `lingerie_color`, `topless_outfit`, `nude_outfit`) and drop accessories that don't belong on a bare body. A locked outfit always beats a tier. A non-`Clothed` tier is recorded in the document `_meta.wardrobe_level` and replayed through the vault and Turnaround (any non-empty tier lifts via `_WARDROBE_LEVEL_KEY`, same shape as `_WARDROBE_KEY`). **`Clothed` is the engine baseline** (API/fallback default, vault-recall default): only the node *widget* defaults to `Lingerie`; a plain document must still recall faithfully clothed.
  - **Explicit action** — `explicit_act` field, 11 sentence-level acts + the neutral "no explicit action" (which stays in the JSON on purpose: a vault round-trip must replay the document byte-identically at a new seed, and an explicit neutral is the difference between "the document decided" and "a fresh draw picked something different"). Prose skips the neutral.
  - **Intimate detail (unreleased, 2.1.0-dev)** — the `Nudity & Intimate` field group: nipple/areola appearance, labia/scrotum + vulva/perineum detail (vaginal opening, urethra, cervix), anus, pubic style + shade, arousal level. Each field declares its visible `tiers` in `data/fields.py` and `generate_character` keeps only what the tier can show — Topless voices the chest fields, Lingerie/Topless/Fully nude voice pubic + arousal, Only Fully nude voices the lower body. Pools are prose phrases in the community tag canon (nipples/areola, labia, cervix, waxed vs full pubis, wetness), re-voiced in natural language for Krea2. A locked detail still voices on an inactive tier (a pin always wins); the Turnaround replay pins unrecorded documents to the `Clothed` baseline so the Lingerie widget default can't re-dress them.
  - **Age band 24–50**, 30–40 weighted heavier via the `age` field weights (0.5 for 24–29 and 41–50, 1.0 for 30–40). Data entries clamped into the band (18→24, 19→25, 20→26, 22→28, 55→45, 60→48, 65→48, 70→50).
  - **Gender** — Female default, `Male` kept for a deliberate override (and to keep the gender-gated constraint rules live when a vault save records a male subject). UI options: `["Female", "Male"]`, default `Female`.
  - **Four nodes only** — `IdentityForge` (main), `IdentityForgeTurnaround`, `IdentityForgeVaultSave`, `IdentityForgeVaultLoad`. The four preset layer node **classes** (Archetype/Cosplayer/Creature/Modifier) are retired: the builder functions (`build_archetype_json`, `build_cosplayer_json`, `build_creature_json`, `build_modifier_json`) remain in their modules, `data/cosplayers.py` / `data/creatures.py` / `data/templates.py` remain (they power the public gallery and the builders), `js/identity_forge_{cosplayer,creature,picker.js}`, `js/identity_forge_picker.css`, `js/identity_forge_roster.json`, and the three corresponding frontend test files are deleted.
  - Everything else from the 1.1.0 lineage: constraint engine, seed reproducibility, Turnaround (rewritten at 0.99.0 to take a resolved character and emit every camera view as a list), the save/load vault with its `"Auto (preset)"` defer sentinels (wardrobe + hair-color scope + now wardrobe_level), the gallery render pipeline with its `--check` gate, release stamps, and both test suites (Python + jsdom).
- **Known gaps / next steps:**
  - **Gallery: the fork's `gh-pages` carries only fork-owned images** — 63 of them (45 cosplay, 18 archetypes; the creatures gallery is all placeholder cards for now). The 2,435 images inherited from the upstream import were **removed from the branch** (2026-08-31) and the per-kind `manifest.json` rebuilt from the branch, so those entries render as placeholder cards, never broken links. **Rule: this fork's `gh-pages` carries only images produced by this fork** — as of the removal it actually does. The ledger is `render_manifest.json`'s `rendered` records vs `FORK_BASELINE` in `scripts/render_gallery.py` (`--check` prints `inherited N` per kind; provenance never reds the gate). Current state: 63 fork-owned, 2,435 inherited and *not yet on the branch* — converge in batches with `python scripts/render_gallery.py --inherited --limit 200 --save-originals --publish`, until it reads `inherited 0` everywhere (each re-render republishes and fills its placeholder). The policy and daily loop live in `gallery/README.md` → "Maintaining the images". **Samples are explicit by pipeline**: `scripts/render_gallery.py` pins `wardrobe_level` per entry (seeded, ~60 % Fully nude / 40 % topless-lingerie-swimwear, never `Clothed`) and a non-neutral `explicit_act`; an archetype/creature preset's locked garment - **and a cosplay costume's** - yields to that tier (`_strip_preset_clothing` walks the whole preset doc, including the `_meta.variants` nesting some presets use; `gallery/README.md` → "The samples are explicit"); the engine also guarantees every tier phrase is non-empty, so no sample can render with zero nudity text. **Prompt sidecars**: every render also writes the exact prompt to `<image>.txt` beside the image, and `publish.py` publishes that `.txt` onto `gh-pages` next to its `.jpeg` (pruned with the image).
  - **`_CATEGORY_FRANCHISES` has two pre-existing adjacent-string-literal typos** (missing commas) — `"Kabuki" "The Owl House"` silently falls through. Left over from 1.1.0, still unfixed at 2.0.0.
  - **`docs/architecture.md` is from the 1.1.0 lineage** — its sections describe the old node set. A full rewrite for 2.0.0 is the standing doc debt; until then, treat the sections on the preset nodes and the picker as historical.
- **Deep docs:** `docs/architecture.md` (deep reference — read before engine or data changes; see gap above), `docs/usage.md`, `docs/cosplayer-notes.md`, `docs/creature-notes.md`, `docs/suggested-additions.md` (backlog), `docs/reference/*.md` (generated, current as of this release).

## Architecture in 60 seconds

- **Data-driven constraint engine.** `data/` modules define fields (all option pools, tier pools, weights), templates, cosplayers, creatures, and cross-field constraints. `nodes/identity_forge.py` is the engine that resolves dropdowns into coherent natural-language prose + structured JSON.
- **Wardrobe ladder.** `data/fields.py` defines `wardrobe_level` (a **control** field) and the five tier-specific pools. The engine branches on the tier in `generate_character`, swapping the resolved fields and dropping accessories that don't fit. The `Nudity & Intimate` group is gated the same way from the data side: each field's `tiers` names the levels that show it, and the engine pops the fields inactive for the resolved tier (a locked value still wins). Prose and JSON both reflect the final tier.
- **ComfyUI frontend.** `js/identity_forge.js` (main node UI, group headers, gender-pool swapping, master buttons, "Fix node (recreate)"), `js/identity_forge_vault.js` (vault save/load UI + manager overlay), `js/identity_forge_recreate.js` (node fixer). Searchable dropdown widget is built in.
- **Generated reference docs.** `docs/reference/*.md` regenerated by `scripts/generate_reference_docs.py` — commit after data changes. `scripts/generate_js_data.py` splices a marker-delimited block into `js/identity_forge.js` (GROUP_ORDER, FIELD_TO_GROUP, GENDER_POOLS). `scripts/dump_frontend_fixtures.py` writes `tests/frontend/fixtures/nodes.json` from the live node schemas.
- **Gallery on `gh-pages`.** Sample renders live on the `gh-pages` branch only; `gallery/.gitignore` blocks images from `main`. `scripts/render_gallery.py --check` is the CI gate; `--missing --save-originals --publish` renders + publishes; the fork-ownership ledger (`FORK_BASELINE`, `is_inherited`, `--inherited`) rides on the same manifest — policy in `gallery/README.md`.

## Layout

| Directory | Purpose |
|-----------|---------|
| `data/` | Fields (all option pools, tier pools, weights), constraints, cosplayers, creatures, templates, user options, release stamps |
| `nodes/` | `identity_forge.py` (engine + main node), `identity_forge_turnaround.py`, `identity_forge_vault_{save,load}.py`, and the four builder modules (cosplayer/creature/archetype/modifier — **builders only, no node classes**) |
| `js/` | ComfyUI frontend (main node UI, vault UI, node fixer) |
| `tests/` | Data validation, engine/vault/turnaround/gallery tests, a `comfy_api` stub (`comfy_stub/`), and a jsdom frontend suite (`frontend/`) |
| `scripts/` | Reference-doc generator, JS-data splicer, frontend-fixture dumper, release stamper, gallery renderer + hash gate |
| `docs/` | Usage, architecture (deep reference, 1.1.0-lineage — see gap above), cosplayer/creature notes, suggested additions |
| `gallery/` | Sample-render manifests + per-kind `publish.py` (images on `gh-pages` only) |

## Build / test / run

```bash
# Validate data integrity
python tests/validate_data.py

# Run all tests (pytest does NOT work here -- it imports comfy_api before the
# stub in tests/__init__.py can register; -t . is required)
python -m unittest discover -s tests -t . -v

# Frontend jsdom suite (npm ci once, then this)
npm run test:frontend

# Regenerate after data changes
python scripts/generate_reference_docs.py
python scripts/stamp_versions.py --stamp     # if roster entries were added

# Regenerate after field-schema changes
python scripts/generate_js_data.py
python scripts/dump_frontend_fixtures.py

# CI checks (all should exit 0)
python scripts/generate_reference_docs.py --check
python scripts/generate_js_data.py --check
python scripts/dump_frontend_fixtures.py --check
python scripts/stamp_versions.py --check
python scripts/render_gallery.py --check

# Render + publish the gallery (needs a running ComfyUI)
# The script auto-detects the ComfyUI instance on localhost:8288 (default)
# or localhost:8188. Override with --url if you need a different one.
python scripts/render_gallery.py --missing --save-originals --publish

# Fork-ownership convergence (in batches, resumable; until --check reads inherited 0)
python scripts/render_gallery.py --inherited --limit 200 --save-originals --publish
```

## Conventions & gotchas

- Zero dependencies. Python ≥3.10. No pip installs required.
- Working principles (from `docs/architecture.md`): no bloat, no duplication, docs stay accurate, tooltips stay current, curate don't hoard.
- **Never read the data layer by importing it in a build script.** Importing runs `apply_user_*` at the bottom of each data module, which merges the maintainer's local `user_options.json` — an import-based generator bakes private entries into a committed, published file. `scripts/stamp_versions.py` parses the source with `ast` instead; `scripts/render_gallery.py` registers the comfy_api stub in-process before importing the builder functions.
- **Tiers are controls, not fields.** `wardrobe_level` is in `_CONTROL_FIELDS` (derived from the `"control": True` marker in `data/fields.py`). It never appears in the JSON group output, never gets randomized, and is always read directly from the widget (or the document's `_meta` on recall). Adding a new tier = add the pool in `data/fields.py`, add the branch in `nodes/identity_forge.py` `generate_character`, add the prose handling in `_format_prose`, and the test in `tests/test_engine.py`. (The gallery render script additionally pins this per entry — see the gallery bullets above.)
- **Wardrobe level beats wardrobe fields, but a locked outfit beats the tier.** A locked costume (e.g. a Cosplayer entry's `outfit_description`) always renders at the tier level even when that tier's own fields are also rolled. This is deliberate — the tier is a *dress code*, not a *garment list*.
- **The neutral `explicit_act` stays in the JSON.** This is load-bearing for vault round-trip byte identity. Do not pop it from `resolved` in the `Clothed` tier either — it's a sentinel, not noise.
- **New non-deferred fields go BEFORE the deferred trio** (`tattoos`, `legwear`, `tattoo_placement`), which must remain the LAST entries of `FIELD_DEFINITIONS` — `_randomize_fields` draws in list order and `_resolve_deferred_fields` runs after it, so anything appended after the trio shifts every seed (pinned by `TattooAndLegwearTests`). Append, never insert mid-list: positional `widgets_values` tolerate appends and nothing else.
- **Gallery images live ONLY on `gh-pages`; the manifest is rebuilt from published files (never deletes).** Editing a roster entry's text while no ComfyUI is running turns the `--check` gate red until the entry is re-rendered — that's the gate working as intended.
- **Fork-only gallery images.** This fork's `gh-pages` carries only images rendered by this fork; `render_manifest.json` is the provenance ledger (`rendered: "pre-existing"` or a date before `FORK_BASELINE` = inherited). `--check` reports the inherited count per kind as information, and `--inherited` renders exactly that set. See `gallery/README.md` → "Maintaining the images".
- **`scripts/render_config.json`** (gitignored) overrides the committed workflow's model/sampler/size settings for this machine's ComfyUI instance. It does not exist on a fresh clone; the script falls back to `gallery/cosplay/Krea2_IdentityForge_CharacterCycle.json`.
- **After a node schema change:** also run `python scripts/dump_frontend_fixtures.py` and commit the refreshed `tests/frontend/fixtures/nodes.json`. Run it with plain `python`, never with a real ComfyUI on `sys.path` — `IdentityForgeVaultLoad` would then list the user's saved characters and commit them.
- **Test fake keys in the secret-scan must be realistic but contain "EXAMPLE"** to hit the allowlist.
- **The data modules are large** (20–30k lines each for cosplayers/creatures/templates) — always grep existing keys before adding an entry.

## Security

This file is **public-safe by default**. Never add local paths, credentials, personal data, infrastructure details, or subscription info.

Deep design rationale, working principles, and data schemas: `docs/architecture.md`.

## Maintenance

**Update rule:** When you change the architecture, build/test commands, or conventions, update this AGENTS.md in the same commit. Keep under 200 lines. Link to `docs/architecture.md` for detail.

**CLAUDE.md:** One-line shim: `@AGENTS.md`.

**No-overlap rule:** Explanatory prose lives in one file. AGENTS.md = agent-facing summary; `docs/architecture.md` = deep reference. Build/test commands may be restated verbatim. Explanatory prose must not be duplicated — link instead.
