#!/usr/bin/env python3
"""Focused contracts for the identity-free obligation-state backoff."""

from copy import deepcopy

from materials_gcts_port_obligation_backoff import (
    PortObligationBackoffLevel, PortObligationBackoffSpec,
    fit_port_obligation_backoff, score_port_obligation_backoff,
    transition_backoff_symbol)


def transition(*, before, after, lost, gained, flag=False):
    relation = {name: {"lost": lost if name == "forward" else 0,
                       "gained": gained if name == "forward" else 0,
                       "after": after if name == "forward" else 0}
                for name in (
                    "backward", "forward", "reverse", "same_parent",
                    "same_source", "touch_parent", "touch_source")}
    flags = {name: bool(flag) for name in (
        "forward_depleted", "no_forward_after", "no_reverse_after",
        "no_touch_source_after", "source_touch_depleted")}
    return {
        "selected_role_transitions": ({
            "role": ("raw-parent-id", (9, 8), "raw-child-id", (7, 6), 5),
            "before": before, "after": after,
            "discharged": max(0, before - after), "produced": gained,
            "relation_counts": relation,
            "contradiction_flags": flags,
        },),
        "selected_pair_relations": (),
    }


def test_backoff_recognizes_unseen_fine_state_without_changing_geometry():
    spec = PortObligationBackoffSpec((
        PortObligationBackoffLevel("exact", 4, 2),
        PortObligationBackoffLevel("role_shape", 2, 2),
        PortObligationBackoffLevel("aggregate", 1, 2),
    ), weakest_states=2)
    rows = (
        {"group": 0, "fit_label": True,
         "transitions": (transition(before=6, after=4, lost=2, gained=0),)},
        {"group": 1, "fit_label": True,
         "transitions": (transition(before=7, after=5, lost=3, gained=0),)},
        {"group": 2, "fit_label": False,
         "transitions": (transition(before=1, after=0, lost=1, gained=0,
                                    flag=True),)},
        {"group": 3, "fit_label": False,
         "transitions": (transition(before=2, after=0, lost=2, gained=0,
                                    flag=True),)},
    )
    model = fit_port_obligation_backoff(rows, spec)
    candidate = (transition(before=9, after=8, lost=4, gained=0),)
    scored = score_port_obligation_backoff(model, candidate)
    assert scored.recognized_fraction == 1.
    assert scored.level_hits[0] == 0
    assert sum(scored.level_hits[1:]) == 1
    assert not model.target_used
    assert not model.candidate_geometry_changed
    assert not model.raw_role_ids_or_coordinates_serialized


def test_symbols_ignore_raw_role_identity_and_fail_on_bad_specs():
    level = PortObligationBackoffLevel("exact", 4)
    first = transition(before=3, after=2, lost=1, gained=0)
    second = deepcopy(first)
    second["selected_role_transitions"][0]["role"] = (
        "different", (100,), "identities", (200,), 99)
    assert transition_backoff_symbol(first, level) == \
        transition_backoff_symbol(second, level)
    try:
        fit_port_obligation_backoff((
            {"group": 0, "fit_label": True, "transitions": (first,)},),
            PortObligationBackoffSpec((level, level)))
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate hierarchy levels must fail closed")


if __name__ == "__main__":
    test_backoff_recognizes_unseen_fine_state_without_changing_geometry()
    test_symbols_ignore_raw_role_identity_and_fail_on_bad_specs()
    print("port-obligation backoff contracts: passed")
