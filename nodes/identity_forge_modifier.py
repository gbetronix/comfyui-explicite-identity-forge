"""IdentityForgeModifier node — prepend a custom descriptor to single elements.

Sometimes you want *one* element to get a stylistic tilt — sci-fi shoes, glowing
earrings, iridescent skin — without theming the whole image. This node lets you
prepend a free-text descriptor in front of a chosen field's (or whole group's)
randomized value. The descriptor lands right before the noun, which is exactly how
text-to-image models pick up textures / genres (great for alien / sci-fi looks).

Wire its ``character_json`` output into the ``archetype_json`` input of an
:class:`~nodes.identity_forge.IdentityForge` node (or chain it after an Archetype /
Cosplayer node via the optional ``upstream`` input — presets stack, this node only
adds modifiers and never fights over field locks).

Usage — one ``key: descriptor`` per line in the ``style_modifiers`` box::

    footwear: sci-fi chrome      # a FIELD -> only the shoes change
    earrings: glowing            # a FIELD -> only the earrings
    skin_tone: iridescent        # a FIELD -> only the skin tone
    Clothing: weathered          # a GROUP -> every clothing item

``key`` is either a **field name** (the same labels shown on the Identity Forge node:
``footwear``, ``skin_tone``, ``hair_color``, ``earrings`` …) for pin-point control,
or a **group header** (``Demographics``, ``Body``, ``Face``, ``Hair``, ``Makeup``,
``Jewelry & Nails``, ``Clothing``, ``Setting & Shot``) to tilt the whole group. Keys
are case-insensitive; a field key beats a group key when both touch the same field.
Blank lines and ``#`` comments are ignored, and unknown keys are skipped with a note.

Modifiers only **decorate values that are present** — they style an element, they do
not force an absent / ``None`` element to appear. Clearing the box (or muting the
node) disables it entirely.

The engine half (:func:`build_modifier_json`) is a pure function, testable without
ComfyUI.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any

# Dual import: package-relative inside ComfyUI, absolute when run standalone.
try:
    from ..data.fields import FIELD_DEFINITIONS
    from .identity_forge import _GROUP_ORDER, _MODIFIERS_DOC_KEY
except ImportError:  # pragma: no cover — standalone/test context
    from data.fields import FIELD_DEFINITIONS
    from nodes.identity_forge import _GROUP_ORDER, _MODIFIERS_DOC_KEY

try:
    from comfy_api.latest import io  # noqa: F401  # availability probe
    _COMFY_AVAILABLE: bool = True
except ImportError:  # pragma: no cover — exercised only outside ComfyUI
    _COMFY_AVAILABLE = False


#: Pre-filled, self-documenting help shown right inside the node's text box. Every
#: line is a comment or blank, so an untouched node emits nothing (passes upstream
#: through). Users delete a ``#`` to switch a line on.
_HELP_DEFAULT = (
    "# Prepend a descriptor to ONE element (or a whole group).\n"
    "# One per line ->  key: descriptor      (delete the # to use a line)\n"
    "# key = a FIELD (footwear, skin_tone, hair_color, earrings, eye_color, ...)\n"
    "#    or a GROUP (Body, Face, Hair, Makeup, Jewelry & Nails, Clothing, Setting & Shot)\n"
    "# Field names are the same labels shown on the Identity Forge node.\n"
    "#\n"
    "# THE ONE RULE: the descriptor goes IN FRONT of the value, it does not\n"
    "# replace it. So keep it to a 1-3 word adjective that reads naturally there.\n"
    "#   good ->  hair_color: living-flame   (becomes 'living-flame auburn')\n"
    "#   bad  ->  hair_style: nest of vipers (becomes 'nest of vipers messy bun')\n"
    "#\n"
    "# --- materials -------------------------------------------------------\n"
    "# skin_tone: iridescent\n"
    "# skin_tone: cracked molten\n"
    "# skin_tone: carved marble\n"
    "# skin_tone: moss-and-lichen\n"
    "# hair_color: living-flame\n"
    "# eye_color: glowing\n"
    "#\n"
    "# --- genres (a whole group at once) ----------------------------------\n"
    "# Clothing: cyberpunk neon\n"
    "# Clothing: baroque gilded\n"
    "# Clothing: post-apocalyptic weathered\n"
    "# footwear: anti-gravity hover\n"
    "#\n"
    "# --- whimsy ----------------------------------------------------------\n"
    "# Makeup: galaxy-glitter\n"
    "# earrings: tiny caged\n"
    "# Setting & Shot: storm-lit\n"
)


def _parse_modifier_text(text: str) -> "OrderedDict[str, str]":
    """Parse the ``key: descriptor`` box into a ``{canonical_key: descriptor}`` map.

    ``key`` matches a :data:`FIELD_DEFINITIONS` field name or a group header from
    :data:`~nodes.identity_forge._GROUP_ORDER`, case-insensitively, and is stored in
    its canonical casing. Blank / ``#`` lines and lines without a ``key: value`` pair
    are skipped; unknown keys are reported and dropped so the emitted payload is clean.
    """
    field_by_lc = {name.lower(): name for name in FIELD_DEFINITIONS}
    group_by_lc = {group.lower(): group for group in _GROUP_ORDER}

    mods: "OrderedDict[str, str]" = OrderedDict()
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            print(f"[IdentityForgeModifier] Skipping line without 'key: descriptor' -> {raw!r}")
            continue
        key, _, descriptor = line.partition(":")
        key, descriptor = key.strip(), descriptor.strip()
        if not key or not descriptor:
            continue
        canonical = field_by_lc.get(key.lower()) or group_by_lc.get(key.lower())
        if canonical is None:
            print(f"[IdentityForgeModifier] Unknown key {key!r}; use a field name or a "
                  f"group header. Skipping.")
            continue
        mods[canonical] = descriptor  # a later line for the same key wins
    return mods


def build_modifier_json(text: str = "") -> str:
    """Return a preset document carrying only a ``_modifiers`` section.

    Empty / all-comment input yields ``"{}"`` so an inactive node simply passes its
    ``upstream`` through (mirrors the other preset nodes' "None" behaviour).
    """
    mods = _parse_modifier_text(text)
    if not mods:
        return "{}"
    document: "OrderedDict[str, Any]" = OrderedDict()
    document[_MODIFIERS_DOC_KEY] = mods
    return json.dumps(document, indent=2)

