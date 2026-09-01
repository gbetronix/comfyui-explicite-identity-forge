"""ExpliciteIdentityForgeCreature node — a non-human *form* layer (animal / monster / alien).

Pick (or randomize) a creature and emit a ``Species & Anatomy`` JSON document that
seeds an :class:`~nodes.identity_forge.ExpliciteIdentityForge` node: a creature head, eyes,
integument (skin / fur / scales / chitin / shell) and optional limbs, tail and wings.
ExpliciteIdentityForge renders the chosen *form* and **suppresses** the human fields it
replaces (a creature head hides the face/hair, a creature integument hides the skin),
while everything not replaced — a wired costume, the surviving body, the scene — still
composes. Wire ``character_json`` into ExpliciteIdentityForge's ``archetype_json`` (or chain it
after an Archetype / Cosplayer via the optional ``upstream`` input; the node closest to
ExpliciteIdentityForge wins on overlap).

**Only-one vs mix-everything.** The ``creature`` widget answers it in one dropdown:
``None`` (off), ``Random - any`` (across every class), ``Random - <class>`` (only
monsters / only insects / only aliens / …), or a specific creature.

**Hybrids / chimeras.** Each anatomy slot (``head``, ``eyes``, ``integument``, ``arms``,
``hands``, ``legs_feet``, ``tail``, ``wings``) can override the base creature — set it to
``Follow base``, ``Random``, or a specific creature. So a praying-mantis body with a
sloth's head is ``creature = praying mantis`` + ``head = sloth``. The free-text
``more_features`` box (``slot: phrase`` lines, or bare extra features) adds unlimited
detail without a wall of widgets.

**Form.** ``Anthropomorphic`` (default) keeps a humanoid silhouette so costumes stay
compatible; ``Feral / full creature`` drops the human clothing/makeup/jewellery for a
true beast; ``Subtle hybrid`` keeps the human and adds the creature as accents. ``Random``
rolls one with the seed.

The engine half (:func:`build_creature_json`) is a pure function, testable without
ComfyUI.
"""
from __future__ import annotations

import json
import random
from collections import OrderedDict
from typing import Any

# Dual import: package-relative inside ComfyUI, absolute when run standalone.
try:
    from ..data.creatures import (
        CREATURES, CREATURE_CLASSES, CREATURE_SLOTS,
        get_creature, get_creature_names, get_creature_names_by_class,
    )
    from .identity_forge import (
        _prepend_descriptor, _SPECIES_GROUP,
        _FORM_ANTHRO, _FORM_FERAL, _FORM_SUBTLE,
    )
except ImportError:  # pragma: no cover — standalone/test context
    from data.creatures import (
        CREATURES, CREATURE_CLASSES, CREATURE_SLOTS,
        get_creature, get_creature_names, get_creature_names_by_class,
    )
    from nodes.identity_forge import (
        _prepend_descriptor, _SPECIES_GROUP,
        _FORM_ANTHRO, _FORM_FERAL, _FORM_SUBTLE,
    )

try:
    from comfy_api.latest import io  # noqa: F401  # availability probe
    _COMFY_AVAILABLE: bool = True
except ImportError:  # pragma: no cover — exercised only outside ComfyUI
    _COMFY_AVAILABLE = False

# --- creature combo sentinels ----------------------------------------------
_NONE = "None"
_RANDOM_ANY = "Random - any"
#: "Random - <class>" -> class, for the only-a-monster / only-an-insect scoping.
_RANDOM_CLASS_LABELS: dict[str, str] = {f"Random - {c}": c for c in CREATURE_CLASSES}

# --- per-slot override sentinels -------------------------------------------
_FOLLOW = "Follow base"
_RANDOM_SLOT = "Random"

# --- detail sentinels ------------------------------------------------------
_AUTO = "Auto"
#: Palette combo: roll a colour from _PALETTES with the seed (works on any creature).
_RANDOM_PALETTE = "Random"
_FINISHES = ["matte", "glossy", "iridescent", "slimy", "bioluminescent",
             "translucent", "metallic", "wet", "fuzzy", "furred", "scaled", "plated",
             "feathered", "mossy", "icy", "spiny", "leathery",
             # 0.67.0 additions (manual-only overrides; Auto never selects a finish,
             # so these widen creative range without touching any randomization).
             "crystalline", "chitinous", "velvety", "molten", "gelatinous",
             "bark-like", "pearlescent", "waxy"]
_PALETTES = ["emerald", "crimson", "sapphire blue", "royal violet", "gold", "obsidian black",
             "bone white", "ash grey", "blood red", "electric blue", "toxic green",
             "iridescent", "chrome", "deep purple", "amber", "teal", "rose pink",
             "silver", "jade", "ruby red", "copper", "ivory"]
_SIZES = ["tiny", "small", "human-sized", "large", "towering"]

# --- form labels (UI) -> canonical tokens (the engine's vocabulary) --------
_FORM_LABEL_ANTHRO = "Anthropomorphic"
_FORM_LABEL_FERAL = "Feral / full creature"
_FORM_LABEL_SUBTLE = "Subtle hybrid"
_FORM_LABEL_RANDOM = "Random"
_FORM_LABEL_TO_TOKEN: dict[str, str] = {
    _FORM_LABEL_ANTHRO: _FORM_ANTHRO,
    _FORM_LABEL_FERAL: _FORM_FERAL,
    _FORM_LABEL_SUBTLE: _FORM_SUBTLE,
}

#: Which human groups/fields a form (and its filled slots) suppress. Mirrors and
#: generalizes ExpliciteIdentityForge's covers_face behaviour: the creature replaces them.
_FORM_SUPPRESS_GROUPS: dict[str, set[str]] = {
    _FORM_ANTHRO: {"Demographics"},
    _FORM_FERAL: {"Demographics", "Makeup", "Jewelry & Nails", "Clothing"},
    _FORM_SUBTLE: set(),
}
#: A feral (non-humanoid) form also drops the humanoid body proportions — a beast has
#: no bust / waist / hips / shoulders. Build / height stay (a "powerful, towering"
#: creature reads fine). Anthro keeps them all (it is humanoid).
#:
#: ``fitness_level`` joined at 0.83.0. The distinction is narrow and worth keeping
#: straight: ``body_type`` states a *shape* ("athletic", "stocky") and reads on anything,
#: but ``fitness_level``'s low values state a human *lifestyle* — a fire elemental
#: described as "sedentary" or "lightly active" is asserting gym habits for a being that
#: has none. Shape stays, lifestyle goes.
_FORM_SUPPRESS_FIELDS: dict[str, set[str]] = {
    _FORM_ANTHRO: set(),
    _FORM_FERAL: {"bust", "waist", "hips", "shoulder_width", "neck_length", "posture",
                  "fitness_level"},
    _FORM_SUBTLE: set(),
}
#: A creature head hides the human face/hair/makeup; an integument hides the skin.
#: arms/hands/legs map to no human field (the body is humanoid), so they add only text.
_SLOT_CONCEAL_GROUPS: dict[str, set[str]] = {"head": {"Face", "Hair", "Makeup"}}
_SLOT_CONCEAL_FIELDS: dict[str, set[str]] = {
    "integument": {"skin_tone", "skin_details", "complexion", "skin_finish", "freckles_density"},
}
#: The Subtle form keeps the human and only *adds* what humans lack (limbs read as
#: creature, plus wings / tail / extras); the conflicting replacers (head, eyes,
#: integument) are dropped so it never co-describes a human and a creature face.
_SUBTLE_DROP_SLOTS: frozenset[str] = frozenset({"head", "eyes", "integument"})

#: The eight anatomy slots exposed as override dropdowns (``extras`` is base-only,
#: plus whatever the free-text box adds).
_OVERRIDE_SLOTS: tuple[str, ...] = (
    "head", "eyes", "integument", "arms", "hands", "legs_feet", "tail", "wings",
)

_MORE_HELP = (
    "# Optional free text — delete these lines to use it.\n"
    "# 'slot: phrase' overrides a slot; a plain line adds an extra feature.\n"
    "# slots: head, eyes, integument, arms, hands, legs_feet, tail, wings\n"
    "#\n"
    "# eyes: six glowing ocelli\n"
    "# a crown of bone spurs\n"
)


# ``_prepend_descriptor`` started here (palette + finish onto an integument slot)
# and now lives in nodes/identity_forge.py, imported above: the engine's Modifier
# path needs the identical article relocation for costume prose. Same function,
# one home.


def _resolve_creature(creature: str, rng: random.Random) -> str | None:
    """Resolve the ``creature`` combo to a concrete name (or ``None``)."""
    if creature == _RANDOM_ANY:
        pool = get_creature_names()
        return rng.choice(pool) if pool else None
    if creature in _RANDOM_CLASS_LABELS:
        pool = get_creature_names_by_class(_RANDOM_CLASS_LABELS[creature])
        if not pool:
            print(f"[ExpliciteIdentityForgeCreature] No creatures available for '{creature}'.")
            return None
        return rng.choice(pool)
    if creature == _NONE or creature not in CREATURES:
        return None
    return creature


def _resolve_slot(
    slot: str, base_name: str | None, selection: str, rng: random.Random
) -> tuple[str | None, str | None]:
    """Resolve one slot to ``(value, source_creature)``.

    ``Follow base`` uses the base creature; ``Random`` picks any creature for that
    slot; a name uses that creature. Returns ``(None, None)`` when nothing applies
    (e.g. the source creature does not fill that slot).
    """
    if selection == _FOLLOW:
        source = base_name
    elif selection == _RANDOM_SLOT:
        pool = get_creature_names()
        source = rng.choice(pool) if pool else None
    elif selection in CREATURES:
        source = selection
    else:
        source = None
    if not source:
        return None, None
    value = get_creature(source).get(slot)
    return (value if isinstance(value, str) and value else None), source


def _parse_more_features(text: str, slots: "OrderedDict[str, str]") -> list[str]:
    """Apply ``more_features`` overrides in place; return loose extra features.

    A ``slot: phrase`` line whose key is a known slot overrides that slot verbatim
    (so the user wins over palette/finish). Any other ``key: phrase`` line or a bare
    line becomes an extra feature appended to ``extras``.
    """
    extras: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key, value = key.strip().lower(), value.strip()
            if not value:
                continue
            if key in CREATURE_SLOTS:
                slots[key] = value
                continue
            extras.append(value)
        else:
            extras.append(line)
    return extras


def _suppression(form_token: str, slots: "OrderedDict[str, str]") -> tuple[list[str], list[str]]:
    """Return ``(suppress_groups, suppress_fields)`` for the form and filled slots."""
    groups = set(_FORM_SUPPRESS_GROUPS.get(form_token, set()))
    fields = set(_FORM_SUPPRESS_FIELDS.get(form_token, set()))
    if form_token != _FORM_SUBTLE:  # Subtle keeps the human; its creature bits are accents
        for slot in slots:
            groups |= _SLOT_CONCEAL_GROUPS.get(slot, set())
            fields |= _SLOT_CONCEAL_FIELDS.get(slot, set())
    return sorted(groups), sorted(fields)


def build_creature_json(
    creature: str,
    seed: int = 0,
    form: str = _FORM_LABEL_ANTHRO,
    head: str = _FOLLOW,
    eyes: str = _FOLLOW,
    integument: str = _FOLLOW,
    arms: str = _FOLLOW,
    hands: str = _FOLLOW,
    legs_feet: str = _FOLLOW,
    tail: str = _FOLLOW,
    wings: str = _FOLLOW,
    integument_finish: str = _AUTO,
    palette: str = _AUTO,
    size_scale: str = _AUTO,
    more_features: str = "",
) -> str:
    """Return the creature preset as a ``Species & Anatomy`` JSON string.

    ``creature`` may be a name, ``"None"`` (→ ``"{}"``), ``"Random - any"`` or
    ``"Random - <class>"``. Each slot override is ``Follow base`` / ``Random`` / a
    name. ``palette`` (default = the integument source's colour) and
    ``integument_finish`` recolour/retexture the integument; ``size_scale`` scales the
    subject; ``more_features`` adds free-text slots/extras. Emits ``"{}"`` when nothing
    is selected, so an inactive node passes its upstream through.
    """
    rng = random.Random(seed)

    form_token = _FORM_LABEL_TO_TOKEN.get(form)
    if form_token is None:  # "Random" (or anything unexpected) -> seed-pick a form
        form_token = rng.choice([_FORM_ANTHRO, _FORM_FERAL, _FORM_SUBTLE])

    base_name = _resolve_creature(creature, rng)
    if base_name is None:  # master switch off ("None") -> inactive, pass upstream through
        return "{}"

    overrides = {
        "head": head, "eyes": eyes, "integument": integument, "arms": arms,
        "hands": hands, "legs_feet": legs_feet, "tail": tail, "wings": wings,
    }
    slots: "OrderedDict[str, str]" = OrderedDict()
    integument_source = base_name
    for slot in CREATURE_SLOTS:
        if slot in _OVERRIDE_SLOTS:
            value, source = _resolve_slot(slot, base_name, overrides[slot], rng)
            if slot == "integument" and source:
                integument_source = source
        elif base_name:  # base-only slots (extras)
            raw = get_creature(base_name).get(slot)
            value = raw if isinstance(raw, str) and raw else None
        else:
            value = None
        if value:
            slots[slot] = value

    # Subtle form keeps the human face/skin: drop the conflicting replacer slots so
    # the result is a human with creature limbs/wings/tail, not two faces.
    if form_token == _FORM_SUBTLE:
        for drop in _SUBTLE_DROP_SLOTS:
            slots.pop(drop, None)

    # Recolour / retexture the integument. Palette resolves last — after every
    # creature / slot / form pick — so a given seed keeps its creature and only the
    # colour shifts: an explicit colour wins; "Random" rolls any palette; "Auto" uses
    # the source creature's own colour, or, for colour-variable species that ship a
    # ``palette_pool`` (most of the roster since 0.38), a seed-varied hue from it, so
    # they are not the same colour every run. The finish then sits outermost.
    if slots.get("integument"):
        src = get_creature(integument_source) if integument_source else {}
        if palette == _RANDOM_PALETTE:
            palette_value = rng.choice(_PALETTES)
        elif palette != _AUTO:
            palette_value = palette
        else:
            pool = src.get("palette_pool")
            palette_value = rng.choice(pool) if pool else src.get("palette")
        if palette_value:
            slots["integument"] = _prepend_descriptor(slots["integument"], palette_value)
        if integument_finish != _AUTO:
            slots["integument"] = _prepend_descriptor(slots["integument"], integument_finish)

    # Free-text overrides win verbatim; loose lines accrue onto extras.
    extras = _parse_more_features(more_features, slots)
    if extras:
        existing = slots.get("extras")
        slots["extras"] = f"{existing}, {', '.join(extras)}" if existing else ", ".join(extras)

    if not slots:  # nothing to render -> inactive, pass upstream through
        return "{}"

    size = size_scale if size_scale != _AUTO else None
    meta: "OrderedDict[str, Any]" = OrderedDict()
    if base_name:
        meta["creature_of"] = base_name
    meta["creature_class"] = get_creature(base_name).get("class", "") if base_name else ""
    meta["form"] = form_token
    if size:
        meta["size"] = size
    suppress_groups, suppress_fields = _suppression(form_token, slots)
    meta["suppress_groups"] = suppress_groups
    meta["suppress_fields"] = suppress_fields

    document: "OrderedDict[str, Any]" = OrderedDict()
    document["_meta"] = meta
    document[_SPECIES_GROUP] = OrderedDict(
        (slot, slots[slot]) for slot in CREATURE_SLOTS if slots.get(slot)
    )
    return json.dumps(document, indent=2)

