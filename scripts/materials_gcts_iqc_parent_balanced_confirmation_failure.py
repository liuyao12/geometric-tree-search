#!/usr/bin/env python3
"""Classify the consumed parent-balanced confirmation as a scorer failure.

The receipt itself is valid and remains immutable.  Its scorer rounded target
and proposal coordinates to eight decimals for exact dictionary lookup, while
the frozen GCTS action representation is six-decimal and the established
colored-position contract is a species-aware ``1e-5`` tolerance.  Because the
target positions were deliberately not retained, the consumed nucleus cannot
be rescored without a second target opening.  Its reported 0/512 is therefore
an invalid harness outcome, not evidence of zero scientific transfer.
"""

from __future__ import annotations

import hashlib
import json

from materials_gcts_iqc_bounded_lineage_value import POSITION_TOLERANCE
from materials_gcts_iqc_parent_balanced_confirmation import \
    load_default_result
from materials_gcts_iqc_parent_balanced_confirmation_preregistration import \
    canonical_json


def evaluate():
    row = load_default_result()
    coordinates = tuple(float(value)
                        for candidate in row["receipt"]["candidates"]
                        for point, _color in candidate["all_actions"]
                        for value in point)
    six_decimal_actions = all(round(value, 6) == value
                              for value in coordinates)
    body = {
        "schema_version": 1,
        "source_result_digest": row["result_digest"],
        "source_receipt_digest": row["receipt_digest"],
        "candidate_actions": len(row["receipt"]["candidates"]) * 12,
        "frozen_action_coordinate_decimals": 6,
        "failed_scorer_coordinate_decimals": 8,
        "authoritative_position_tolerance": POSITION_TOLERANCE,
        "all_frozen_action_coordinates_are_six_decimal":
            six_decimal_actions,
        "target_positions_serialized": False,
        "second_target_open_or_rescore_allowed": False,
        "reported_zero_exact_candidates_scientifically_interpretable": False,
        "failure_class": "confirmation scorer precision mismatch",
        "fresh_scientific_supply_gate_passed": False,
        "retry_same_nucleus_allowed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            not body["all_frozen_action_coordinates_are_six_decimal"] or
            body["target_positions_serialized"] or
            body["second_target_open_or_rescore_allowed"] or
            body["reported_zero_exact_candidates_scientifically_interpretable"] or
            body["fresh_scientific_supply_gate_passed"] or
            body["retry_same_nucleus_allowed"]):
        raise AssertionError("parent-balanced failure classification drift")
    return row


if __name__ == "__main__":
    print(json.dumps(validate_result(evaluate()), indent=2, sort_keys=True))
