"""Roster for the FETISH gallery: one showcase entry per explicit act.

Shared by ``scripts/render_gallery.py`` (the render/manifest pipeline) and
``gallery/fetish/build_manifest.py`` (the site manifest + publisher), so one
curated table serves both.

``ENTRIES`` is the SINGLE source of truth, and it is an explicit literal:
``scripts/stamp_versions.py`` reads it with ``ast`` (importing the module would
also run ``data.fields`` and merge the maintainer's local user_options.json,
which must never leak into the published manifests). If the engine's
``explicit_act`` pool and this table drift apart, ``entries()`` raises at
import time -- the gallery can never silently show a stale set of acts.

Acts marked ``"nude_act": True`` are the breast/vagina plays: the engine's own
minimum-undress rule resolves them Fully nude, which is the state the showcase
image shows. The camera-intimacy plays (face/hands/saliva) stay tier-neutral.
"""
from __future__ import annotations

from data.fields import FIELD_DEFINITIONS

#: display name -> {act: the sentence the engine voices, nude_act: the engine
#: resolves it Fully nude}. The display names ARE the dropdown labels and the
#: published filenames, so they must be unique and filename-safe -- entries()
#: enforces both. Pool order matches the engine's own ``explicit_act`` pool.
ENTRIES: dict[str, dict] = {
    "Fingering": {"act": "fingering herself", "nude_act": False},
    "Pillow ride": {"act": "riding a fluffy pillow", "nude_act": False},
    "Spanking": {"act": "spanking herself", "nude_act": False},
    "Hand down her torso": {"act": "running one hand slowly down her own torso", "nude_act": False},
    "Lip bite": {"act": "biting her lower lip lightly", "nude_act": False},
    "Ice cube": {"act": "sinking an ice cube between her lips", "nude_act": False},
    "Arch back": {"act": "arching backward with one hand behind her head", "nude_act": False},
    "Crouch, hips arched": {"act": "crouching over the edge of the bed, hips arched", "nude_act": False},
    "Kneeling, back to camera": {"act": "kneeling with her back to the camera, hips lifted", "nude_act": False},
    "Sipping from a glass": {"act": "sipping from a tall glass, lips parted around the rim", "nude_act": False},
    "Rolling in the sheets": {"act": "rolling in the sheets, half buried under the duvet", "nude_act": False},
    "Face-sitting": {"act": "face-sitting the camera, weight rolling slow side to side", "nude_act": False},
    "Golden shower": {"act": "urinating over the camera, a slow golden shower", "nude_act": False},
    "Foot licking": {"act": "licking her own feet, slow and deliberate", "nude_act": False},
    "Finger licking": {"act": "licking each fingertip in turn, mouth closing around each one", "nude_act": False},
    "Breast licking": {"act": "licking her own breasts, tongue tracing the areola in slow circles", "nude_act": True},
    "Spitting": {"act": "gathering spit and spitting it at the camera", "nude_act": False},
    "Crotch press": {"act": "crotch pressing against the camera, hips rolling", "nude_act": True},
    "Fisting the camera": {"act": "slowly working the camera with one fist, lips parted", "nude_act": False},
    "Breathing on camera": {"act": "blowing hot breath on the camera, a long slow exhale", "nude_act": False},
    "Drooling": {"act": "drooling, thick saliva trailing from her lips onto the camera", "nude_act": False},
    "Kissing the camera": {"act": "kissing the camera open-mouthed, tongue slow", "nude_act": False},
    "Biting the camera": {"act": "biting the camera firmly, teeth sinking in", "nude_act": False},
    "Moaning at the camera": {"act": "moaning loudly at the camera, voice rough", "nude_act": False},
    "Milking": {"act": "clenching her breast and milking through her knuckles", "nude_act": True},
    "Nipple peak": {"act": "sucking her own nipple hard into a peak", "nude_act": True},
    "Breast bouncing": {"act": "bouncing her breasts, each bounce heavy", "nude_act": True},
    "Breast milk": {"act": "pressing a thin stream of breast milk onto the camera", "nude_act": True},
    "Dripping": {"act": "dripping, each drop landing on the camera", "nude_act": True},
    "Squirting": {"act": "squirt play, gushing clear fluid onto the camera", "nude_act": True},
    "Labia spread": {"act": "spreading her labia with her fingers, wet and dripping", "nude_act": True},
    "Crotch slap": {"act": "repeatedly slapping her own crotch, each slap echoing", "nude_act": True},
}


def _pool_acts() -> list[str]:
    acts = FIELD_DEFINITIONS["explicit_act"]["female_options"]
    return [a for a in acts if a != "no explicit action"]


def _nude_acts() -> frozenset[str]:
    return frozenset(FIELD_DEFINITIONS["explicit_act"].get("implies_fully_nude", ()))


def entries() -> dict[str, dict]:
    """The roster, validated against the engine's live pool.

    Raises if a display name is duplicated, if any pool act has no showcase
    entry, or if the ``nude_act`` flags disagree with the field's own
    ``implies_fully_nude`` set -- so the gallery, the stamper and the engine
    can never silently disagree.
    """
    pool = _pool_acts()
    nude = _nude_acts()
    by_act = {d["act"]: (name, d) for name, d in ENTRIES.items()}

    if sorted(by_act) != sorted(pool):
        missing = [a for a in pool if a not in by_act]
        extra = [a for a in by_act if a not in pool]
        raise KeyError(f"roster/pool drift -- missing: {missing[:4]}, extra: {extra[:4]}")
    if len(ENTRIES) != len(set(ENTRIES)):
        raise KeyError("duplicate display names in the fetish roster")
    for name, d in ENTRIES.items():
        expect = d["act"] in nude
        if bool(d.get("nude_act")) != expect:
            raise KeyError(f"nude_act flag disagrees with the field for {name!r}")
    return dict(ENTRIES)


def entry_names() -> list[str]:
    return list(entries())
