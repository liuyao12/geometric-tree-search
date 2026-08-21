#!/usr/bin/env python3
"""Freeze full-frontier relational port-discharge counters for wide IQC states.

Selected port identities stay bounded by the proposal marking.  For each one,
the builder scans the complete before/after semantic role multisets and records
only fixed relation categories: reciprocal, forward/backward continuation,
shared endpoint, and endpoint touch.  Background role identities and absolute
coordinates are never serialized.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_typed_port_discharge_dataset import (
    _role_counts, typed_transition)
import materials_gcts_iqc_wide_typed_port_discharge_dataset as wide
from materials_gcts_iqc_wide_rollback_portfolio import (
    EXPECTED_AUDIT_DIGEST as WIDE_PORTFOLIO_DIGEST)


RELATIONS = (
    "reverse", "forward", "backward", "same_parent", "same_source",
    "touch_parent", "touch_source",
)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_relational_port_discharge_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "913893f99e269771489c7fcb41cd910d73df7034fee1f495f97e9f06913a22cd"
EXPECTED_DATASET_DIGEST = \
    "aecda621ca1f0960cdd14a74995983d2483a94ed52051bd273082d0cc59ab3de"


def _endpoint(role, side):
    return ((role[0], tuple(role[1])) if side == "parent"
            else (role[2], tuple(role[3])))


def _relations(selected, other):
    parent = _endpoint(selected, "parent")
    source = _endpoint(selected, "source")
    other_parent = _endpoint(other, "parent")
    other_source = _endpoint(other, "source")
    return {
        "reverse": (other_parent == source and other_source == parent
                    and int(other[4]) == int(selected[4])),
        "forward": other_parent == source,
        "backward": other_source == parent,
        "same_parent": other_parent == parent,
        "same_source": other_source == source,
        "touch_parent": other_parent == parent or other_source == parent,
        "touch_source": other_parent == source or other_source == source,
    }


def _relation_counts(selected, counts):
    result = {name: 0 for name in RELATIONS}
    for role, multiplicity in counts.items():
        flags = _relations(selected, role)
        for name in RELATIONS:
            result[name] += int(multiplicity) * int(flags[name])
    return result


def relational_transition(before_frontier, selected_point, after_frontier):
    row = typed_transition(before_frontier, selected_point, after_frontier)
    before = _role_counts(before_frontier)
    after = _role_counts(after_frontier)
    for selected in row["selected_role_transitions"]:
        role = (str(selected["role"][0]), tuple(selected["role"][1]),
                str(selected["role"][2]), tuple(selected["role"][3]),
                int(selected["role"][4]))
        left = _relation_counts(role, before)
        right = _relation_counts(role, after)
        selected["relation_counts"] = {
            name: {
                "before": left[name], "after": right[name],
                "lost": max(0, left[name] - right[name]),
                "retained": min(left[name], right[name]),
                "gained": max(0, right[name] - left[name]),
            } for name in RELATIONS}
        selected["contradiction_flags"] = {
            "no_reverse_after": right["reverse"] == 0,
            "no_forward_after": right["forward"] == 0,
            "no_touch_source_after": right["touch_source"] == 0,
            "forward_depleted": right["forward"] < left["forward"],
            "source_touch_depleted": (
                right["touch_source"] < left["touch_source"]),
        }
    selected_roles = [
        (str(item["role"][0]), tuple(item["role"][1]),
         str(item["role"][2]), tuple(item["role"][3]), int(item["role"][4]))
        for item in row["selected_role_transitions"]]
    row["selected_pair_relations"] = tuple({
        "left_rank": left,
        "right_rank": right,
        **_relations(selected_roles[left], selected_roles[right]),
    } for left in range(len(selected_roles))
      for right in range(left + 1, len(selected_roles)))
    return row


def build_dataset(*, workers=1):
    payloads, portfolio = wide._payloads()
    relational_payloads = tuple((*payload, True) for payload in payloads)
    groups = (tuple(wide._evaluate_group(payload)
                    for payload in relational_payloads)
              if workers == 1 else wide._parallel_groups(
                  relational_payloads, workers))
    body = {
        "schema_version": 1,
        "source_wide_portfolio_audit_digest": portfolio["audit_digest"],
        "development_groups": len(groups),
        "retained_candidates": sum(len(group["rows"]) for group in groups),
        "maximum_retained_candidates": max(
            len(group["rows"]) for group in groups),
        "rollout_horizon": wide.ROLLOUT_HORIZON,
        "relation_categories": RELATIONS,
        "groups": groups,
        "selected_role_cohort_untruncated": True,
        "full_background_role_multiset_scanned": True,
        "background_role_identities_serialized": False,
        "proper_rotation_quotiented_upstream": True,
        "candidate_geometry_unchanged": True,
        "target_used_for_rollouts": False,
        "rollout_target_crop_constructed": False,
        "labels_joined_after_geometry_freeze": True,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
    }
    return {**body, "dataset_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("relational fixture byte drift")
    row = json.loads(gzip.decompress(raw))
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            != digest or body["source_wide_portfolio_audit_digest"] !=
            WIDE_PORTFOLIO_DIGEST or body["retained_candidates"] != 120
            or tuple(body["relation_categories"]) != RELATIONS
            or not body["full_background_role_multiset_scanned"]
            or body["background_role_identities_serialized"]
            or body["target_used_for_rollouts"]
            or body["rollout_target_crop_constructed"]
            or not body["labels_joined_after_geometry_freeze"]):
        raise AssertionError("relational discharge dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("relational discharge digest drift")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    row = build_dataset(workers=max(1, args.workers))
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
