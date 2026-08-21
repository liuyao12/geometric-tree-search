#!/usr/bin/env python3
"""Exploratory group-heldout audit of finite IQC obligation dynamics."""

from __future__ import annotations

from dataclasses import asdict
import argparse
from collections import Counter
import hashlib
import json
import random

from materials_gcts_iqc_relational_port_discharge_dataset import (
    load_default_dataset)
from materials_gcts_iqc_relational_port_rule import (
    SHUFFLES, SHUFFLE_SEED, load_default_result as load_relational_result)
from materials_gcts_port_obligation_automaton import (
    PortObligationAutomatonSpec, fit_port_obligation_automaton,
    score_port_obligation_trajectory)


SPEC = PortObligationAutomatonSpec(
    count_cap=4, minimum_groups=1, weakest_states=4)


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _rows():
    dataset = load_default_dataset()
    geometry = []
    labels = {}
    for group in dataset["groups"]:
        for row in group["rows"]:
            key = (int(group["group"]), int(row["stable_index"]))
            geometry.append({
                "group": key[0], "stable_index": key[1],
                "transitions": tuple(row["typed_transitions"]),
            })
            labels[key] = (bool(row["exact"]), int(row["correct_sites"]))
    geometry = tuple(sorted(geometry, key=lambda row: (
        row["group"], row["stable_index"])))
    digest = _digest(tuple((row["group"], row["stable_index"],
                            row["transitions"]) for row in geometry))
    return dataset, geometry, labels, digest


def _labelled(geometry, labels):
    return tuple({**row, "fit_label": labels[
        row["group"], row["stable_index"]][0]} for row in geometry)


def _heldout(geometry, labels):
    selected = []
    groups = tuple(sorted({row["group"] for row in geometry}))
    for heldout in groups:
        training = tuple(row for row in geometry if row["group"] != heldout)
        model = fit_port_obligation_automaton(
            _labelled(training, labels), SPEC)
        candidates = tuple(row for row in geometry
                           if row["group"] == heldout)
        ranked = tuple(sorted(candidates, key=lambda row: (
            -score_port_obligation_trajectory(
                model, row["transitions"])[0], row["stable_index"])))
        selected.append(ranked[0])
    supplied = {group for (group, _index), (exact, _sites) in labels.items()
                if exact}
    exact = sum(labels[row["group"], row["stable_index"]][0]
                for row in selected if row["group"] in supplied)
    sites = sum(labels[row["group"], row["stable_index"]][1]
                for row in selected)
    return tuple(selected), exact, sites


def _shuffle(labels, trial):
    rng = random.Random(f"{SHUFFLE_SEED}:obligation-automaton:{trial}")
    result = dict(labels)
    for group in sorted({key[0] for key in labels}):
        keys = sorted(key for key in labels if key[0] == group)
        values = [labels[key] for key in keys]
        rng.shuffle(values)
        result.update(zip(keys, values))
    return result


def evaluate():
    dataset, geometry, labels, geometry_digest = _rows()
    # All transition sequences freeze before development labels are attached.
    selected, exact, sites = _heldout(geometry, labels)
    null = tuple(_heldout(geometry, _shuffle(labels, trial))[1]
                 for trial in range(SHUFFLES))
    p_value = (1 + sum(value >= exact for value in null)) / (SHUFFLES + 1)
    final_model = fit_port_obligation_automaton(
        _labelled(geometry, labels), SPEC)
    prior = load_relational_result()
    supplied_groups = len({group for (group, _index), (value, _sites)
                           in labels.items() if value})
    maximum_correct_sites = sum(max(
        sites for (row_group, _index), (_exact, sites) in labels.items()
        if row_group == group) for group in sorted(
            {key[0] for key in labels}))
    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "trajectory_geometry_digest": geometry_digest,
        "candidate_count": len(geometry),
        "group_count": len({row["group"] for row in geometry}),
        "supplied_groups": supplied_groups,
        "spec": asdict(SPEC),
        "finite_state_count": len(final_model.states),
        "finite_state_group_support_histogram": tuple(sorted(Counter(
            len(row.training_groups) for row in final_model.states).items())),
        "model_digest": final_model.model_digest,
        "heldout_selected_indices": tuple(
            (row["group"], row["stable_index"]) for row in selected),
        "heldout_selected_exact_supplied_groups": exact,
        "heldout_selected_correct_sites": sites,
        "maximum_available_correct_sites": maximum_correct_sites,
        "prior_relational_selected_exact_supplied_groups":
            prior["nested_selected_exact_supplied_groups"],
        "prior_relational_selected_correct_sites":
            prior["nested_selected_correct_sites"],
        "shuffle_trials": SHUFFLES,
        "shuffle_exact_counts": null,
        "shuffle_exact_median": sorted(null)[SHUFFLES // 2],
        "shuffle_exact_maximum": max(null),
        "shuffle_upper_tail_p": p_value,
        "weakest_link_sequence_improves_prior": bool(
            exact > prior["nested_selected_exact_supplied_groups"] and
            sites >= prior["nested_selected_correct_sites"]),
        "all_trajectory_geometry_frozen_before_label_join": True,
        "one_balanced_vote_per_observed_group_per_state": True,
        "role_identities_or_absolute_coordinates_serialized": False,
        "candidate_geometry_changed": False,
        "exploratory_spec_not_preregistered": True,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["obligation_automaton_gate_passed"] = bool(
        exact == supplied_groups and sites == maximum_correct_sites and
        p_value <= .05 and not body["exploratory_spec_not_preregistered"])
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("obligation automaton passes" if
           report["obligation_automaton_gate_passed"] else
           "obligation automaton remains exploratory"))


if __name__ == "__main__":
    main()
