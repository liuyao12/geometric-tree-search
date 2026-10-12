"""Metadata-only immutable V1 -> V2 source repair. No scientific imports."""
from pathlib import Path
import difflib
import hashlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
old = ROOT / '.gcts-active/family-proposal-rl-small-source-20261012/family_learned_overlay_v1.py'
raw = old.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'f11ca5a1113c66108af4d61995463b2525dd9b4f6f2ac469c6d514eaa3dca2f6'
text = raw.decode()
text = text.replace("VERSION = 'paired-learned-whole-family-overlay-v1'", "VERSION = 'paired-learned-whole-family-overlay-v2'")
anchor = """        policy = None
        if prepared['needs_one_draw']:
"""
replacement = """        # The prepared object is a caller-owned transport value, not authority.
        # Rebuild the complete canonical menu from the SAME verified state and
        # immutable inputs; neither a supplied hash nor a draw flag can make
        # altered features/action IDs authoritative. No resync occurs here,
        # because that would change the exact state being checked.
        expected_needs_one_draw = current.kind == 'branch' and self.active_id is None
        expected_menu = (self.features.menu_features(
            self._feature_graph(), self.recipes, self.graph.formulas,
            self.records, [hint.data() for hint in self.control.states],
            [current.kind, current.row, current.count, current.generation])
            if expected_needs_one_draw else None)
        if (prepared['needs_one_draw'] is not expected_needs_one_draw
                or self.core.canonical(prepared['menu']) != self.core.canonical(expected_menu)):
            raise ValueError('prepared complete menu or draw requirement differs from verified state')
        policy = None
        if expected_needs_one_draw:
"""
assert text.count(anchor) == 1
text = text.replace(anchor, replacement)
text = text.replace("            menu = prepared['menu']\n", "            menu = expected_menu\n")
target = HERE / 'family_learned_overlay_v2.py'
target.write_text(text)
(HERE / 'overlay-v1-to-v2.diff').write_text(''.join(difflib.unified_diff(
    raw.decode().splitlines(keepends=True), text.splitlines(keepends=True),
    fromfile=str(old.relative_to(ROOT)), tofile=str(target.relative_to(ROOT)))))
