#!/usr/bin/env python3
"""Contract for the unopened recurrent-supply confirmation."""

from materials_gcts_iqc_recurrent_supply_confirmation_preregistration import (
    audit)


def main():
    report = audit()
    assert report.source_hashes_match
    assert report.training_groups == 10
    assert report.development_validation_groups == 8
    assert report.prototype_minimum_groups == 2
    assert report.successor_dependency == "both ordered affine endpoints"
    assert not report.seed_or_target_materialized
    assert not report.candidate_or_score_computed
    assert len(report.manifest_digest) == 64
    print(report.manifest_digest)


if __name__ == "__main__":
    main()
