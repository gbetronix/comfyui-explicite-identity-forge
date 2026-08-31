"""Guard the gallery render gate in ``scripts/render_gallery.py``.

The gate's whole value rests on three properties, and each one has a way of
quietly breaking:

* ``--check`` passes on the committed tree. If it does not, either somebody
  edited an entry without re-rendering (which is the gate doing its job) or the
  manifest was seeded at the wrong moment (which is the gate lying).
* ``entry_hash`` is deterministic across processes and actually reacts to the
  text it claims to cover. A hash over the wrong thing still produces a stable
  hex string and looks entirely healthy.
* Importing the module is inert. It is imported by CI, which installs nothing
  and has no ComfyUI and no network, so any HTTP or node import at module scope
  would turn every CI run into a network call.
"""
from __future__ import annotations

import importlib
import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import render_gallery  # noqa: E402


class CheckPassesTests(unittest.TestCase):
    def test_check_is_clean_on_the_committed_tree(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = render_gallery.main(["--check"])
        self.assertEqual(
            code, 0,
            "scripts/render_gallery.py --check is failing on the committed "
            "tree:\n" + buffer.getvalue(),
        )

    def test_the_manifest_covers_every_kind(self) -> None:
        manifest = render_gallery.load_manifest()
        self.assertEqual(manifest["schema_version"], render_gallery.MANIFEST_VERSION)
        for kind in render_gallery.KINDS:
            self.assertTrue(
                manifest["entries"].get(kind),
                f"the manifest has no entries recorded for {kind}",
            )

    def test_the_render_block_is_not_part_of_any_entry_record(self) -> None:
        # Deliberate: ~2,150 images predate this pipeline and were rendered
        # under settings nobody recorded, so folding render settings into the
        # per-entry hash would mark every one of them stale. If this ever
        # starts failing, read the note on entry_hash before "fixing" it.
        manifest = render_gallery.load_manifest()
        for kind, records in manifest["entries"].items():
            for name, record in records.items():
                self.assertEqual(
                    set(record) - {"hash", "rendered", "seed"}, set(),
                    f"{kind}/{name} records more than a hash, a date and an "
                    f"optional re-rolled seed",
                )


class EntryHashTests(unittest.TestCase):
    def test_hash_is_stable_across_calls(self) -> None:
        first = render_gallery.entry_hash("cosplay", "2B")
        second = render_gallery.entry_hash("cosplay", "2B")
        self.assertEqual(first, second)

    def test_hash_changes_when_a_costume_string_changes(self) -> None:
        from data.cosplayers import COSPLAYERS

        name = "2B"
        before = render_gallery.entry_hash("cosplay", name)
        original = COSPLAYERS[name]["costume"]
        try:
            COSPLAYERS[name]["costume"] = original + " and a scarf"
            self.assertNotEqual(before, render_gallery.entry_hash("cosplay", name))
        finally:
            COSPLAYERS[name]["costume"] = original
        self.assertEqual(before, render_gallery.entry_hash("cosplay", name))

    def test_hash_covers_the_merged_archetype_costume(self) -> None:
        from data.templates import ARCHETYPES

        name = next(iter(ARCHETYPES))
        before = render_gallery.entry_hash("archetypes", name)
        entry = ARCHETYPES[name]
        entry["__probe__"] = "x"
        try:
            self.assertNotEqual(before, render_gallery.entry_hash("archetypes", name))
        finally:
            entry.pop("__probe__")

    def test_seed_is_deterministic_and_matches_the_recorded_formula(self) -> None:
        import hashlib

        name = "Jack Skellington"
        expected = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:15], 16)
        self.assertEqual(render_gallery.entry_seed(name), expected)
        self.assertEqual(
            render_gallery.load_manifest()["seed_formula"],
            render_gallery.SEED_FORMULA,
        )


class GalleryShotPoolTests(unittest.TestCase):
    """Regression: ``_gallery_shot`` must always pin a real camera angle.

    ``shot_type``'s option list carries "Random" (its control value) and
    "None" (its omit sentinel) alongside actual framings. The pool filter
    excluded "Random" but not "None" -- so on the seeds that landed on it,
    the gallery render passed shot_type="None" into IdentityForge.execute,
    which (a non-Random widget value always beats a preset lock) silently
    discarded whatever shot_type the archetype/cosplayer itself locked,
    with no framing at all. Caught via ``Kendo Practitioner`` (locked to
    "full body shot") rendering as an extreme close-up twice in a row.
    """

    def test_never_returns_the_omit_sentinel_or_control_value(self) -> None:
        for seed in range(500):
            shot = render_gallery._gallery_shot(seed)
            self.assertNotEqual(shot, "None", f"seed {seed} picked the omit sentinel")
            self.assertNotEqual(shot, "Random", f"seed {seed} picked the control value")
            self.assertNotIn(shot, render_gallery._BACK_FACING_SHOTS,
                              f"seed {seed} picked a back-facing shot")


class ImportIsInertTests(unittest.TestCase):
    """The module must import with no ComfyUI, no network and no side effects."""

    def test_importing_opens_no_socket(self) -> None:
        # A subprocess, because render_gallery is already imported in this one:
        # a module runs its top-level code once per process, so patching sockets
        # here would prove nothing about import time.
        probe = (
            "import socket, sys\n"
            "class Blocked(socket.socket):\n"
            "    def connect(self, *a, **k):\n"
            "        raise AssertionError('render_gallery opened a socket at import')\n"
            "socket.socket = Blocked\n"
            f"sys.path.insert(0, {str(ROOT)!r})\n"
            f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
            "import render_gallery\n"
            "assert 'comfy_api' not in sys.modules, 'ComfyUI imported at import time'\n"
            "print('ok')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ok", result.stdout)

    def test_check_needs_no_comfyui(self) -> None:
        # survey() reads the data layer only. If a node module ever creeps into
        # that path, CI (which has no ComfyUI at all) is where it would surface.
        importlib.reload(render_gallery)
        results = render_gallery.survey()
        self.assertEqual(set(results), set(render_gallery.KINDS))

    def test_the_manifest_file_is_valid_json_with_a_trailing_newline(self) -> None:
        raw = render_gallery.MANIFEST.read_text(encoding="utf-8")
        self.assertTrue(raw.endswith("\n"))
        json.loads(raw)


class InheritedLedgerTests(unittest.TestCase):
    """The fork-ownership rule: this fork's gh-pages carries only fork-produced
    images. ``render_manifest.json`` is the ledger; ``FORK_BASELINE`` is the

    record; ``--inherited`` is the convergence pass. Provenance is informational
    to ``--check`` (it must not turn a clean tree red), but the selection and
    the ledger itself must be exact.
    """

    def test_baseline_is_an_iso_date(self) -> None:
        import datetime as _dt

        _dt.date.fromisoformat(render_gallery.FORK_BASELINE)

    def test_preexisting_and_pre_baseline_records_are_inherited(self) -> None:
        for rendered in ("pre-existing", "2026-08-09", "2026-08-30"):
            record = {"hash": "x", "rendered": rendered}
            self.assertTrue(
                render_gallery.is_inherited(record),
                f"{rendered!r} must count as inherited",
            )

    def test_baseline_day_and_later_are_fork_owned(self) -> None:
        for rendered in ("2026-08-31", "2026-09-15"):
            record = {"hash": "x", "rendered": rendered}
            self.assertFalse(
                render_gallery.is_inherited(record),
                f"{rendered!r} must count as fork-owned",
            )

    def test_missing_record_and_unknown_values_are_inherited(self) -> None:
        self.assertTrue(render_gallery.is_inherited(None))
        self.assertTrue(render_gallery.is_inherited({"hash": "x"}))

    def test_baseline_is_a_parameter_not_a_mystery(self) -> None:
        record = {"hash": "x", "rendered": "2025-01-01"}
        self.assertTrue(render_gallery.is_inherited(record, baseline="2026-01-01"))
        self.assertFalse(render_gallery.is_inherited(record, baseline="2025-01-01"))

    def test_survey_reports_the_inherited_bucket_exactly(self) -> None:
        results = render_gallery.survey(render_gallery.KINDS)
        recorded_all = render_gallery.load_manifest()["entries"]
        for kind in render_gallery.KINDS:
            entries = render_gallery.entries_for(kind)
            recorded = recorded_all.get(kind, {})
            expected = sorted(
                name for name in entries
                if render_gallery.is_inherited(recorded.get(name))
            )
            self.assertEqual(results[kind]["inherited"], expected)
            # Partition property: every entry is exactly one of inherited or fork-owned.
            self.assertEqual(
                len(results[kind]["inherited"]) + (len(entries)
                                                   - len(results[kind]["inherited"])),
                len(entries),
            )

    def test_inherited_selection_targets_exactly_the_bucket(self) -> None:
        import argparse

        args = argparse.Namespace(entry=[], missing=False, stale=False, inherited=True)
        kinds = render_gallery.KINDS
        chosen = render_gallery._targets(args, kinds)
        results = render_gallery.survey(kinds)
        self.assertEqual(
            sorted(chosen),
            sorted((kind, name)
                   for kind in kinds
                   for name in results[kind]["inherited"]),
        )

    def test_check_notes_convergence_but_stays_green(self) -> None:
        # Inherited images are provenance, not correctness: the committed tree
        # (which still carries upstream renders) must exit 0 and name the pass.
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = render_gallery.main(["--check"])
        self.assertEqual(code, 0, buffer.getvalue())
        output = buffer.getvalue()
        self.assertIn("inherited", output.lower())
        self.assertIn("Fork-ownership converges", output)


if __name__ == "__main__":
    unittest.main()


class ExplicitSampleTests(unittest.TestCase):
    """The showcase rule: every sample is at least partially nude.

    The pinned tier is the dress code. A preset lock of the garment -- at any
    depth in its document -- would keep the sample clothed and break the rule
    the gallery is built for, so the strip must reach every nesting level and
    the finished prose must actually carry the tier.
    """

    @staticmethod
    def _all_keys(node, out):
        if isinstance(node, dict):
            for k, v in node.items():
                out.append(k)
                ExplicitSampleTests._all_keys(v, out)
        elif isinstance(node, list):
            for v in node:
                ExplicitSampleTests._all_keys(v, out)
        return out

    def test_strip_reaches_locks_at_every_depth(self) -> None:
        raw = {
            "outfit_description": "flat lock",
            "Clothing": {
                "outfit_style": "locked",
                "bag": "a leather satchel",
                "expression": "kept",
            },
            "_meta": {
                "archetype": "kept",
                "variants": {
                    "Female": {"outfit_description": "nested lock",
                               "hair_color": "kept"},
                    "Male": {"footwear": "locked", "mood": "kept"},
                },
            },
        }
        stripped = json.loads(render_gallery._strip_preset_clothing(json.dumps(raw)))
        keys = self._all_keys(stripped, [])
        for gone in ("outfit_description", "outfit_style", "bag", "footwear"):
            self.assertNotIn(gone, keys, f"{gone} survived the strip")
        for kept in ("expression", "hair_color", "mood", "archetype"):
            self.assertIn(kept, keys, f"{kept} was lost to the strip")

    def test_variant_archetype_loses_costume_keeps_face(self) -> None:
        # B-Boy / B-Girl keeps its costume ONLY inside _meta.variants.* --
        # the nesting that once let a "Fully nude" sample render in track pants.
        render_gallery._register_comfy_stub()
        from nodes.identity_forge_archetype import build_archetype_json

        name = "B-Boy / B-Girl"
        preset = build_archetype_json(name, render_gallery.entry_seed(name, 0),
                                      "Essentials")
        value = getattr(preset, "args", preset)
        if isinstance(value, tuple):
            value = value[0]
        if not isinstance(value, str):
            value = value[0] if isinstance(value, (list, tuple)) else str(value)
        stripped = json.loads(render_gallery._strip_preset_clothing(value))
        keys = self._all_keys(stripped, [])
        self.assertNotIn("outfit_description", keys)
        self.assertIn("hair_color", keys)

    def test_pinned_tier_is_visible_in_the_prose(self) -> None:
        # Entries that once rendered fully clothed. For each, the prose must
        # carry its own seeded tier: a Fully nude body says "nothing", a
        # Topless one says "bare from the waist up", and the lingerie and
        # swimwear tiers show their own pool wording.
        render_gallery._register_comfy_stub()
        from nodes.identity_forge import FIELD_DEFINITIONS

        cases = [
            ("archetypes", "B-Boy / B-Girl"),
            ("archetypes", "Figure Skater"),
            ("archetypes", "1970s Used Car Salesman"),
            ("archetypes", "1950s Diner Waitress"),
            ("cosplay", "Yzma"),
        ]
        for kind, name in cases:
            seed = render_gallery.entry_seed(name, 0)
            tier = render_gallery._gallery_wardrobe(seed)
            prose = render_gallery.resolve_prose(kind, name)
            self.assertIn("wears", prose, (name, tier))
            if tier == "Fully nude":
                self.assertRegex(prose, r"\bnothing\b", (name, tier))
            elif tier == "Topless":
                self.assertIn("bare from the waist up", prose)
            else:
                field = ("lingerie_style" if tier == "Lingerie"
                         else "swimwear_style")
                pool = FIELD_DEFINITIONS[field]["female_options"]
                self.assertTrue(any(opt in prose for opt in pool),
                                f"{name}: no {field} wording found")
