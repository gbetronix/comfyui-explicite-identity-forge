"""Deterministic gallery seeding tests.

The gallery is the node's own randomisation published as examples, so the seed
is the entire reproducibility contract: same seed + same entry + same machine
must render the same body, pose and setting, or the published images can never
again be explained by their prompts.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import tests  # noqa: F401  registers the comfy_api stub before any import
import render_gallery  # noqa: E402  (script, imported by file path)


class GallerySeedingTests(unittest.TestCase):
    """The kind + entry + seed triple is the unit of reproducibility."""

    def test_seed_is_reproducible_per_kind_and_entry(self):
        seed_a = render_gallery._gallery_shot(42)
        seed_b = render_gallery._gallery_shot(42)
        self.assertEqual(seed_a, seed_b)

    def test_different_entries_get_different_seeds(self):
        shots = {render_gallery._gallery_shot(s) for s in (42, 43, 44)}
        self.assertGreaterEqual(len(shots), 2, "three seeds collapsed to one shot")

    def test_wardrobe_and_act_are_deterministic_pool_values(self):
        from data.fields import FIELD_DEFINITIONS
        tier_opts = ["Clothed", "Swimwear", "Lingerie", "Topless", "Fully nude"]
        act_opts = set(FIELD_DEFINITIONS["explicit_act"]["female_options"])
        for seed in (0, 7, 99):
            self.assertIn(render_gallery._gallery_wardrobe(seed), tier_opts)
            self.assertIn(render_gallery._gallery_act(seed), act_opts)


class NewGalleriesRosterTests(unittest.TestCase):
    """The fetish and nudity rosters are complete and pool-validated at import."""

    def test_fetish_roster_covers_the_pool_and_flags_nude_acts(self):
        entries = render_gallery.entries_for("fetish")
        self.assertEqual(len(entries), 32)
        self.assertGreaterEqual(
            sum(1 for d in entries.values() if d.get("nude_act")), 10)

    def test_nudity_roster_covers_every_tier(self):
        entries = render_gallery.entries_for("nudity")
        tiers = {d["tier"] for d in entries.values()}
        self.assertEqual(tiers, {"Swimwear", "Lingerie", "Topless", "Fully nude"})
        self.assertGreaterEqual(len(entries), 50)


if __name__ == "__main__":
    unittest.main()
