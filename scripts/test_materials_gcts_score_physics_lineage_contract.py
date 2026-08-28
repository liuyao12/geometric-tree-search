import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/score-normalization.mjs").read_text()


def test_every_score_term_resolves_to_a_manifest_layer():
    score_ids = set(re.findall(r'scoreTerm\("([^"]+)"', APP))
    mapping_block = MODULE.split("export const SCORE_PHYSICS_MANIFEST_IDS", 1)[1].split("});", 1)[0]
    mapping_ids = set(re.findall(r'^\s*(?:"([^"]+)"|([a-z][a-z-]*)):', mapping_block, re.MULTILINE))
    mapping_ids = {quoted or bare for quoted, bare in mapping_ids}
    assert mapping_ids == score_ids

    manifest_ids = set(re.findall(r'\{ id: "([^"]+)", process:', APP))
    mapped_targets = set(re.findall(r': "([^"]+)"', mapping_block))
    assert mapped_targets <= manifest_ids
    assert len(mapped_targets) >= 20

    assert "score term ${term.id} has no physics-manifest source" in APP
    assert "normalization ledger cannot resolve physics layer ${audit.physicsManifestId}" in APP


if __name__ == "__main__":
    test_every_score_term_resolves_to_a_manifest_layer()
    print("score-to-physics lineage contract passed")
