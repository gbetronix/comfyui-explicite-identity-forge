# Explicite Prompt Generator for ComfyUI

**Coherent, seed-reproducible adult women (24–50) at every level of explicitness — built from dropdowns, no prompt engineering required.**

A standalone rework of the Identity Forge prompt engine: the same
constraint logic and seed
reproducibility, now tuned to a single job — generating women aged 24 to 50
(30–40 weighted heavier), from a fully clothed portrait down through swimwear,
lingerie, topless and fully nude, with optional explicit-action sentences.

Queue once and meet one woman. Queue again and meet another — never the same
two prompts, never a contradictory one (no heels with gym kit, no makeup
sentence on a bare face, no jewelry on a fully nude body).

## What you can steer

- **Wardrobe level** — *Clothed · Swimwear · Lingerie · Topless · Fully nude*.
  Each level has its own curated pools (bikinis and one-pieces, lace sets and
  sheer mesh, bottoms and bare-chest looks, and fully-nude options down to a
  single small worn item). Levels compose with location, lighting, pose and
  composition — an indoor lingerie shot gets indoor lighting, not an open sky.
- **Explicit action** — eleven optional sentence-level actions (straddling,
  spread, tongue-out, fingers-in-hair, kneeling behind, …) plus the neutral
  default "no explicit action". The act lands at the end of the prompt
  alongside the pose, and never contradicts the wardrobe level.
- **Age 24–50** — the generator is explicitly adult; 30–40 rolls twice as
  often as the rest of the range, per the age weights.
- **Everything else** — demographics, body, face, hair, makeup, jewelry,
  clothing (at the Clothed level), pose, expression, lighting, location,
  composition and shot type. Each field is `Random` (roll it), a locked value
  (that trait is yours) or `None` (omit it).
- **Seed reproducibility** — the same seed + same locks is the same woman.
  Vault-save the one you want.
- **Gender** — the generator is woman-first (default Female); a Male override
  still exists for the occasions you want one.

## The nodes (four)

| Node | What it does |
| --- | --- |
| **Explicite Prompt Generator** (`ExpliciteIdentityForge`) | The generator. All fields above, constraint engine, dual `prompt_text` / `prompt_json` output. |
| **Turnaround** (`ExpliciteIdentityForgeTurnaround`) | Takes a resolved character's `prompt_json` and emits every camera view of it (front, three-quarter, profile, back) as a list — one queue renders the whole reference set. |
| **Character Vault Save** (`ExpliciteIdentityForgeVaultSave`) | Save a generated character (prose + exact locks + thumbnail) to a local vault. |
| **Character Vault Load** (`ExpliciteIdentityForgeVaultLoad`) | Recall a saved character; the document replays its exact controls, so a Nudist-l… wardrobe-level save comes back at the same wardrobe level. |

### Sample prompts

A Lingerie-level roll, seed 41:

> A 33-year-old Brazilian woman with an hourglass build … She wears a black
> lace bra and matching briefs in a muted plum. The framing is a full body
> shot, three-quarter angle … soft window light from the left … her
> expression is sultry … She is on her knees at the edge of the bed, arching
> her back toward the camera, looking back over her shoulder.

A Fully nude roll, seed 7:

> A 46-year-old Polish woman with a full figured build … She is wearing a
> gold body chain across her hips, nothing else. … The framing is a close-up
> shot, facing the camera … warm tungsten practical light … She is lying on
> her back on dark sheets, head tilted back, eyes closed.

(Both abridged; the real prose keeps the skin tone, hair, face and makeup
clauses the constraint engine guarantees.)

## Install

The pack is dependency-free. Drop it into ComfyUI's `custom_nodes/` folder —
or point ComfyUI Manager at the repo. No pip installs, no API keys, fully
offline.

```
git clone <this repo> ComfyUI/custom_nodes/comfyui-explicite-prompt-generator
```

Restart ComfyUI; the four nodes appear under `conditioning/`.

## Quick start

1. Add an **Explicite Prompt Generator** node.
2. Set **wardrobe_level** to the explicitness you want. Lock the few traits
   you care about; leave the rest on `Random`.
3. Queue. Copy `prompt_text` into your text encoder. Same seed + same locks
   = same woman, every time.
4. Found the one? **Character Vault Save** → name it. **Character Vault Load**
   brings it back byte-for-byte.

## Must-know

- **Wardrobe level beats the wardrobe fields.** A locked outfit always beats
  a wardrobe level (`Clothed` generation locks in over any supplied costume
  the same way it does in the normal run). A costume locked to a Lingerie
  level renders *that costume*, at that level of dress.
- **Accessories follow the level.** Fully nude drops earrings/necklace/rings/
  bracelets except body chains; Topless keeps ear and neck jewelry but drops
  the wrist and hand set. The engine enforces this so you never prompt
  "knee-high boots with a naked torso".
- **The explicit action is the last sentence** and only appears when you lock
  it. The neutral "no explicit action" default produces a plain pose — the
  wardrobe level already carries the nudity.
- **Seed drift is intentional and measured.** Changing a lock changes the RNG
  stream. That's by design: locks are identity, not post-processing.

## How the constraint engine works

`data/` ships the rules: per-gender option pools, concept-share weights
(feminine-coded items dominate the Female pool at realistic proportions), and
cross-field exclusions (no heels + sportswear, no makeup on a shaven face
when the field is locked absent, …). The engine resolves your dropdowns into
a coherent set — no two contradictory traits in one prompt — then renders it
as natural prose *and* a structured JSON document that the Turnaround, Vault
and Stylebook interop all read.

The full reference — schemas, working principles, the "Never negate" rule,
measured open questions — lives in [`docs/architecture.md`](docs/architecture.md).

## Development

```bash
python tests/validate_data.py                      # data integrity
python -m unittest discover -s tests -t . -v       # Python suite (pytest doesn't work here; -t . is load-bearing)
npm run test:frontend                              # jsdom suite (npm ci once first)
python scripts/generate_reference_docs.py          # after data changes
python scripts/generate_js_data.py                 # after field-schema changes
python scripts/dump_frontend_fixtures.py           # after node schema changes
python scripts/stamp_versions.py --stamp           # after roster changes
python scripts/render_gallery.py --check           # gallery render gate (network-free)
```

## License

MIT — a standalone rework of the original Identity Forge pack (EnragedAntelope).
