#!/usr/bin/env python3

from materials_gcts_cdyb_confirmatory_execution_erratum import (
    ERRATUM, ERRATUM_DIGEST, audit_erratum)


def test_abort_was_predata_and_correction_is_narrow():
    audit = audit_erratum()
    assert len(ERRATUM_DIGEST) == 64
    assert audit["pretarget_abort_only"]
    assert ERRATUM.target_factory_calls == 0
    assert not ERRATUM.confirmatory_seed_accessed
    assert not ERRATUM.scientific_trial_consumed
    assert "v1 geometry protocol" in ERRATUM.sole_permitted_correction


if __name__ == "__main__":
    test_abort_was_predata_and_correction_is_narrow()
    print("CdYb confirmatory execution erratum: passed")
