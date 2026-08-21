"""Fast no-atom contract for the site-resolved IQC confirmation."""

import hashlib
from pathlib import Path

from materials_gcts_iqc_site_resolved_confirmation_preregistration import (
    EXPECTED_MANIFEST_DIGEST, REQUIRED_CENTER_SEPARATION,
    SOURCE_FILE_SHA256S, audit)


ROOT = Path(__file__).resolve().parent
MODULE = ROOT / \
    "materials_gcts_iqc_site_resolved_confirmation_preregistration.py"


def test_confirmation_is_frozen_before_atom_access() -> None:
    row = audit()
    source = MODULE.read_text(encoding="utf-8")

    assert row.manifest_digest == EXPECTED_MANIFEST_DIGEST
    assert row.confirmation_center == (0., -120., -160.)
    assert row.center_selection_reproduced
    assert row.minimum_consumed_center_separation > \
        REQUIRED_CENTER_SEPARATION
    assert row.self_fed_waves == 3
    assert row.required_exact_sites == 9
    assert row.frozen_model_digest == \
        "891e8badab355abfdeeed5d83a05c62cf34f22962cf193d3ead283a43c6afccc"
    assert not row.oracle_cropper_executor_or_target_imported
    assert not row.confirmation_atoms_candidates_scores_or_labels_materialized
    assert not row.fresh_confirmation_claimed

    assert "oracle_patch_fast" not in source
    assert " import _crop" not in source
    assert "_complete_states_at_radius" not in source
    for name, expected in SOURCE_FILE_SHA256S:
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected


if __name__ == "__main__":
    test_confirmation_is_frozen_before_atom_access()
    print("site-resolved confirmation preregistration: passed")
