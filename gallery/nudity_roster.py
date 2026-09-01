"""Roster for the NUDITY gallery: one showcase entry per wardrobe tier pool value.

Coverage is the wardrobe ladder itself, tier by tier: every value of
``swimwear_style``, ``lingerie_style`` (paired deterministically with a colour,
so each look renders the same way every time), ``topless_outfit``,
``nude_outfit`` -- plus the Nudity & Intimate group (``pubic_style``,
``arousal_level``, ``nipple_appearance``, ``labia_appearance``) shown at
Fully nude. ``Clothed`` carries no nude-specific fields on purpose (it is the
engine baseline), so it has no gallery of its own.

Shared by ``scripts/render_gallery.py`` and ``gallery/nudity/build_manifest.py``.
``ENTRIES`` is an explicit literal that ``scripts/stamp_versions.py`` reads with
``ast`` (importing the module would merge the maintainer's user_options.json);
``entries()`` re-derives the same table from the live pools and raises if the
two drift apart, so a pool change can never ship a stale dropdown.
"""
from __future__ import annotations

from data.fields import FIELD_DEFINITIONS

#: (field, display label) pairs this gallery showcases, in site order.
LOOKS = (
    ("swimwear_style", "Swimwear"),
    ("lingerie_style", "Lingerie"),
    ("topless_outfit", "Topless"),
    ("nude_outfit", "Nude look"),
    ("pubic_style", "Pubic"),
    ("arousal_level", "Arousal"),
    ("nipple_appearance", "Nipples"),
    ("labia_appearance", "Labia"),
)

#: The wardrobe tier each field is voiced at (the renderer locks the
#: wardrobe_level to match, so the pool value is actually described).
TIER_OF = {
    "swimwear_style": "Swimwear",
    "lingerie_style": "Lingerie",
    "topless_outfit": "Topless",
    "nude_outfit": "Fully nude",
    "pubic_style": "Fully nude",
    "arousal_level": "Fully nude",
    "nipple_appearance": "Fully nude",
    "labia_appearance": "Fully nude",
}

#: The explicit name -> data table (``scripts/stamp_versions.py`` reads it with
#: ``ast``).
ENTRIES: dict[str, dict] = {
    "A red string bikini": {"tier": "Swimwear", "label": "Swimwear"},
    "A black low-rise bikini": {"tier": "Swimwear", "label": "Swimwear"},
    "A pastel bandeau bikini": {"tier": "Swimwear", "label": "Swimwear"},
    "A navy one-piece swimsuit": {"tier": "Swimwear", "label": "Swimwear"},
    "A leopard-print one-piece": {"tier": "Swimwear", "label": "Swimwear"},
    "A sheer black monokini": {"tier": "Swimwear", "label": "Swimwear"},
    "A white ribbed sports two-piece": {"tier": "Swimwear", "label": "Swimwear"},
    "A champagne satin longline-bikini-style one-piece": {"tier": "Swimwear", "label": "Swimwear"},
    "A crimson plunge-front one-piece": {"tier": "Swimwear", "label": "Swimwear"},
    "A mint cut-out high-cut bikini": {"tier": "Swimwear", "label": "Swimwear"},
    "A black-and-white gingham two-piece": {"tier": "Swimwear", "label": "Swimwear"},
    "A smoky grey neoprene one-piece": {"tier": "Swimwear", "label": "Swimwear"},
    "Lace bra and matching briefs · Black": {"tier": "Lingerie", "label": "Lingerie"},
    "Silk babydoll · Champagne": {"tier": "Lingerie", "label": "Lingerie"},
    "Lace bodysuit with matching garter and sheer stockings · Ivory": {"tier": "Lingerie", "label": "Lingerie"},
    "Satin teddy · Red": {"tier": "Lingerie", "label": "Lingerie"},
    "Mesh bodystocking over a low-rise thong · Burgundy": {"tier": "Lingerie", "label": "Lingerie"},
    "Silk negligee · Emerald": {"tier": "Lingerie", "label": "Lingerie"},
    "Lace bralette and high-waisted briefs · Sapphire blue": {"tier": "Lingerie", "label": "Lingerie"},
    "Satin robe left open over a matching bra and briefs · Smoke-grey": {"tier": "Lingerie", "label": "Lingerie"},
    "Lace push-up bra and lace briefs · Hot-pink": {"tier": "Lingerie", "label": "Lingerie"},
    "Velour lingerie set · Cream": {"tier": "Lingerie", "label": "Lingerie"},
    "Bodysuit with strappy back and matching garter belt · Deep plum": {"tier": "Lingerie", "label": "Lingerie"},
    "Lace plunge bra and string briefs · Solar orange": {"tier": "Lingerie", "label": "Lingerie"},
    "Satin chemise · Black": {"tier": "Lingerie", "label": "Lingerie"},
    "Sheer camisole and matching briefs · Champagne": {"tier": "Lingerie", "label": "Lingerie"},
    "A black string bikini bottom, bare from the waist up": {"tier": "Topless", "label": "Topless"},
    "White cotton briefs, bare from the waist up": {"tier": "Topless", "label": "Topless"},
    "Cutoff denim shorts, bare from the waist up": {"tier": "Topless", "label": "Topless"},
    "A tiny black hipster, bare from the waist up": {"tier": "Topless", "label": "Topless"},
    "A low-rise thong, bare from the waist up": {"tier": "Topless", "label": "Topless"},
    "Black lace briefs, bare from the waist up": {"tier": "Topless", "label": "Topless"},
    "A white satin skirt that rides high on the hips, bare from the waist up": {"tier": "Topless", "label": "Topless"},
    "Black leather hot pants, bare from the waist up": {"tier": "Topless", "label": "Topless"},
    "Nothing at all": {"tier": "Fully nude", "label": "Nude look"},
    "Nothing but a thin gold anklet": {"tier": "Fully nude", "label": "Nude look"},
    "Nothing but strappy heels": {"tier": "Fully nude", "label": "Nude look"},
    "Nothing but sheer stockings pinned to a garter belt": {"tier": "Fully nude", "label": "Nude look"},
    "Nothing but a delicate body chain": {"tier": "Fully nude", "label": "Nude look"},
    "Nothing but a single long earring catching the light": {"tier": "Fully nude", "label": "Nude look"},
    "Smoothly shaved, natural skin tone": {"tier": "Fully nude", "label": "Pubic"},
    "Smoothly waxed to a minimal line": {"tier": "Fully nude", "label": "Pubic"},
    "Neatly trimmed along a soft, natural line": {"tier": "Fully nude", "label": "Pubic"},
    "Lightly trimmed, with natural growth": {"tier": "Fully nude", "label": "Pubic"},
    "Full, natural and untrimmed": {"tier": "Fully nude", "label": "Pubic"},
    "Serene and unhurried": {"tier": "Fully nude", "label": "Arousal"},
    "Subtly flushed, a little breathless": {"tier": "Fully nude", "label": "Arousal"},
    "Clearly aroused, flushed and softly glistening": {"tier": "Fully nude", "label": "Arousal"},
    "Drenched and slick with arousal": {"tier": "Fully nude", "label": "Arousal"},
    "Soft, understated nipples": {"tier": "Fully nude", "label": "Nipples"},
    "Slightly prominent, pink nipples": {"tier": "Fully nude", "label": "Nipples"},
    "Raised, delicate-looking nipples": {"tier": "Fully nude", "label": "Nipples"},
    "Turgid, sensitive-looking nipples": {"tier": "Fully nude", "label": "Nipples"},
    "Slightly inverted nipples": {"tier": "Fully nude", "label": "Nipples"},
    "Long, slender nipples": {"tier": "Fully nude", "label": "Nipples"},
    "Soft, naturally proportioned labia": {"tier": "Fully nude", "label": "Labia"},
    "Full, softly rounded labia majora": {"tier": "Fully nude", "label": "Labia"},
    "Modest, closely fitted labia": {"tier": "Fully nude", "label": "Labia"},
    "Slightly prominent inner labia": {"tier": "Fully nude", "label": "Labia"},
    "Full, softly parted labia": {"tier": "Fully nude", "label": "Labia"},
}


def _title(value: str) -> str:
    text = " ".join(value.split())
    return text[0].upper() + text[1:]


def _pool_entries() -> dict[str, dict]:
    out = {}
    seen = set()
    for field, label in LOOKS:
        for i, value in enumerate(FIELD_DEFINITIONS[field]["female_options"] or []):
            name = _title(value)
            if field == "lingerie_style":
                name += " \u00b7 " + _title(
                    FIELD_DEFINITIONS["lingerie_color"]["female_options"][i % 12])
            if name in seen:
                name += f" {i + 1}"
            seen.add(name)
            out[name] = {"tier": TIER_OF[field], field: value, "label": label}
    return out


def entries() -> dict[str, dict]:
    """The live pool-derived table, validated against ENTRIES."""
    live = _pool_entries()
    if set(live) != set(ENTRIES):
        raise KeyError(
            "roster/pool drift -- missing: %r, unknown: %r"
            % (sorted(set(live) - set(ENTRIES))[:4],
               sorted(set(ENTRIES) - set(live))[:4]))
    return live


def entry_names() -> list[str]:
    return list(entries())
